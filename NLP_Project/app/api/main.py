# """
# FastAPI Main Application
# Handles PDF upload, text extraction, and query processing
# """
# import uvicorn
# from fastapi import FastAPI, UploadFile, File, HTTPException
# from fastapi.responses import JSONResponse
# from fastapi.middleware.cors import CORSMiddleware
# from pydantic import BaseModel, Field
# from typing import Optional, List
# import pymupdf
# import re

# from app.vector_store import batch_store_in_weaviate, get_object_count
# from app.rag import process_query
# from app.llm import check_api_connection

# app = FastAPI(
#     title="Legal RAG API",
#     description="RAG system for Indian Legal Documents (BNS, BNSS, BSA)",
#     version="1.0.0"
# )

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# # Regex patterns for document parsing
# SECTION_AND_SUBSECTION = re.compile(r"^(\d+)\.\s*\((\d+)\)")
# SECTION_PATTERN = re.compile(r"^(\d+)\.")
# SUBSECTION_PATTERN = re.compile(r"^\((\d+)\)")
# CLAUSE_PATTERN = re.compile(r"^\([a-z]\)")
# EXPLANATION_PATTERN = re.compile(r"^(Explanation|Illustration)", re.IGNORECASE)

# # Noise filters
# NOISE_PATTERNS = [
#     "MINISTRY", "REGISTERED NO", "NEW DELHI", "EXTRAORDINARY",
#     "GOVERNMENT", "GAZETTE", "PUBLISHED BY AUTHORITY", "Hkkx", "fnlEcj"
# ]

# # Tag keywords for categorization
# TAG_KEYWORDS = {
#     "vehicle": ["motor vehicle", "transport"],
#     "computer": ["IT", "cybercrime"],
#     "murder": ["criminal law", "offence"],
#     "mutiny": ["military law"],
#     "document": ["records", "evidence"],
#     "child": ["juvenile", "minor"],
#     "death": ["homicide", "general"],
#     "court": ["judiciary", "legal system"]
# }

# # Pydantic models for API
# class QueryRequest(BaseModel):
#     query: str = Field(..., description="User's question about legal documents")
#     top_k: Optional[int] = Field(5, description="Number of relevant documents to retrieve", ge=1, le=20)

# class QueryResponse(BaseModel):
#     query: str
#     answer: str
#     sources: List[dict]
#     context_used: bool
#     num_sources: Optional[int] = 0

# class HealthResponse(BaseModel):
#     status: str
#     message: str
#     database_count: int
#     gemini_api_status: bool


# def assign_tags(text: str):
#     """Assign tags based on keyword matching."""
#     tags = []
#     for keyword, taglist in TAG_KEYWORDS.items():
#         if keyword.lower() in text.lower():
#             tags.extend(taglist)
#     return list(set(tags))


# def is_noise(line: str):
#     """Check if a line is noise/header/footer."""
#     if any(noise in line for noise in NOISE_PATTERNS):
#         return True
#     if re.fullmatch(r"[-_]{5,}", line.replace(" ", "")):
#         return True
#     if len(line.strip()) < 2:
#         return True
#     return False


# @app.get("/", response_model=HealthResponse)
# def health_check():
#     """Health check endpoint with system status."""
#     try:
#         db_count = get_object_count()
#         gemini_status = check_api_connection()
        
#         return HealthResponse(
#             status="healthy",
#             message="Legal RAG API is running",
#             database_count=db_count,
#             gemini_api_status=gemini_status
#         )
#     except Exception as e:
#         return HealthResponse(
#             status="partial",
#             message=f"Service running with issues: {str(e)}",
#             database_count=0,
#             gemini_api_status=False
#         )


# @app.post("/extract-text", response_class=JSONResponse)
# async def extract_hierarchical_json(file: UploadFile = File(...)):
#     """
#     Extract text from PDF and store in vector database.
#     Processes legal documents with section/subsection structure.
#     """
#     try:
#         contents = await file.read()
#         pdf_doc = pymupdf.open(stream=contents, filetype="pdf")
#         file_name = file.filename
#         corpus = []
#         current_section = None
#         current_section_obj = None
#         current_subsection_obj = None
        
#         # Collect all subsections for batch storage
#         all_subsections = []

#         for page_num, page in enumerate(pdf_doc):
#             lines = page.get_text("text").split("\n")
#             for line in lines:
#                 line = line.strip()
#                 if not line or is_noise(line):
#                     continue

#                 # Section + Subsection e.g., 1. (1)
#                 if SECTION_AND_SUBSECTION.match(line):
#                     sec, subsec = SECTION_AND_SUBSECTION.match(line).groups()
#                     if current_section != sec:
#                         if current_section_obj:
#                             current_section_obj["tags"] = list({tag for s in current_section_obj["subsections"] for tag in s["tags"]})
#                             corpus.append(current_section_obj)
#                         current_section = sec
#                         current_section_obj = {"section": sec, "heading": None, "tags": [], "subsections": []}
                    
#                     current_subsection_obj = {
#                         "section": sec,
#                         "number": subsec,
#                         "content": line,
#                         "tags": assign_tags(line),
#                         "page": page_num + 1,
#                         "file": file_name
#                     }
#                     current_section_obj["subsections"].append(current_subsection_obj)
#                     all_subsections.append(current_subsection_obj)

#                 # Subsection only e.g., (1)
#                 elif SUBSECTION_PATTERN.match(line):
#                     subsec = SUBSECTION_PATTERN.match(line).group(1)
#                     current_subsection_obj = {
#                         "section": current_section,
#                         "number": subsec,
#                         "content": line,
#                         "tags": assign_tags(line),
#                         "page": page_num + 1,
#                         "file": file_name
#                     }
#                     if current_section_obj:
#                         current_section_obj["subsections"].append(current_subsection_obj)
#                         all_subsections.append(current_subsection_obj)

#                 # Continuation text
#                 else:
#                     if current_subsection_obj:
#                         current_subsection_obj["content"] += " " + line
#                         current_subsection_obj["tags"].extend(assign_tags(line))
#                         current_subsection_obj["tags"] = list(set(current_subsection_obj["tags"]))

#         if current_section_obj:
#             current_section_obj["tags"] = list({tag for s in current_section_obj["subsections"] for tag in s["tags"]})
#             corpus.append(current_section_obj)

#         # Store all subsections in Weaviate
#         print(f"📦 Storing {len(all_subsections)} subsections in Weaviate...")
#         batch_store_in_weaviate(all_subsections)
#         print(f"✅ Successfully stored {len(all_subsections)} subsections")

#         return JSONResponse(
#             status_code=200,
#             content={
#                 "message": f"Successfully processed {file_name}",
#                 "total_sections": len(corpus),
#                 "total_subsections": len(all_subsections),
#                 "data": corpus
#             }
#         )
#     except Exception as e:
#         print(f"❌ Error: {str(e)}")
#         raise HTTPException(status_code=500, detail=str(e))


# @app.post("/query", response_model=QueryResponse)
# async def query_legal_documents(request: QueryRequest):
#     """
#     Query the legal document database using RAG.
    
#     This endpoint:
#     1. Searches for relevant content in the vector database
#     2. Uses Gemini to generate a contextual response
#     3. Returns the answer with source citations
#     """
#     try:
#         if not request.query or len(request.query.strip()) == 0:
#             raise HTTPException(status_code=400, detail="Query cannot be empty")
        
#         print(f"\n{'='*60}")
#         print(f"📝 New Query: {request.query}")
#         print(f"{'='*60}")
        
#         # Process query using RAG
#         result = process_query(request.query, top_k=request.top_k)
        
#         return QueryResponse(**result)
        
#     except Exception as e:
#         print(f"❌ Error processing query: {e}")
#         raise HTTPException(status_code=500, detail=f"Error processing query: {str(e)}")


# @app.get("/stats")
# async def get_statistics():
#     """Get statistics about the database."""
#     try:
#         count = get_object_count()
#         return {
#             "total_documents": count,
#             "status": "active"
#         }
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))


# if __name__ == "__main__":
#     uvicorn.run("app.api.main:app", host="0.0.0.0", port=3000, reload=True)



















"""
FastAPI Main Application with Conversational RAG Support
Handles PDF upload, text extraction, and conversational query processing
"""
import uvicorn
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, List, Dict
import pymupdf
import re
from collections import defaultdict
import uuid

from app.vector_store import batch_store_in_weaviate, get_object_count
from app.rag import process_query
from app.llm import check_api_connection

app = FastAPI(
    title="Legal RAG API",
    description="RAG system for Indian Legal Documents (BNS, BNSS, BSA) with Conversational Support",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory storage for conversation sessions
# In production, use Redis or a database
conversation_sessions: Dict[str, List[Dict]] = defaultdict(list)

# Regex patterns for document parsing
SECTION_AND_SUBSECTION = re.compile(r"^(\d+)\.\s*\((\d+)\)")
SECTION_PATTERN = re.compile(r"^(\d+)\.")
SUBSECTION_PATTERN = re.compile(r"^\((\d+)\)")
CLAUSE_PATTERN = re.compile(r"^\([a-z]\)")
EXPLANATION_PATTERN = re.compile(r"^(Explanation|Illustration)", re.IGNORECASE)

# Noise filters
NOISE_PATTERNS = [
    "MINISTRY", "REGISTERED NO", "NEW DELHI", "EXTRAORDINARY",
    "GOVERNMENT", "GAZETTE", "PUBLISHED BY AUTHORITY", "Hkkx", "fnlEcj"
]

# Tag keywords for categorization
TAG_KEYWORDS = {
    "vehicle": ["motor vehicle", "transport"],
    "computer": ["IT", "cybercrime"],
    "murder": ["criminal law", "offence"],
    "mutiny": ["military law"],
    "document": ["records", "evidence"],
    "child": ["juvenile", "minor"],
    "death": ["homicide", "general"],
    "court": ["judiciary", "legal system"]
}

# Pydantic models for API
class QueryRequest(BaseModel):
    query: str = Field(..., description="User's question about legal documents")
    top_k: Optional[int] = Field(5, description="Number of relevant documents to retrieve", ge=1, le=20)
    session_id: Optional[str] = Field(None, description="Session ID for conversation tracking")
    conversation_history: Optional[List[Dict]] = Field(None, description="Manual conversation history (alternative to session_id)")

class QueryResponse(BaseModel):
    query: str
    answer: str
    sources: List[dict]
    context_used: bool
    num_sources: Optional[int] = 0
    session_id: Optional[str] = None
    conversation_aware: Optional[bool] = False

class SessionResponse(BaseModel):
    session_id: str
    message: str

class HealthResponse(BaseModel):
    status: str
    message: str
    database_count: int
    gemini_api_status: bool
    active_sessions: int


def assign_tags(text: str):
    """Assign tags based on keyword matching."""
    tags = []
    for keyword, taglist in TAG_KEYWORDS.items():
        if keyword.lower() in text.lower():
            tags.extend(taglist)
    return list(set(tags))


def is_noise(line: str):
    """Check if a line is noise/header/footer."""
    if any(noise in line for noise in NOISE_PATTERNS):
        return True
    if re.fullmatch(r"[-_]{5,}", line.replace(" ", "")):
        return True
    if len(line.strip()) < 2:
        return True
    return False


@app.get("/", response_model=HealthResponse)
def health_check():
    """Health check endpoint with system status."""
    try:
        db_count = get_object_count()
        gemini_status = check_api_connection()
        
        return HealthResponse(
            status="healthy",
            message="Legal RAG API is running with Conversational Support",
            database_count=db_count,
            gemini_api_status=gemini_status,
            active_sessions=len(conversation_sessions)
        )
    except Exception as e:
        return HealthResponse(
            status="partial",
            message=f"Service running with issues: {str(e)}",
            database_count=0,
            gemini_api_status=False,
            active_sessions=0
        )


@app.post("/session/new", response_model=SessionResponse)
async def create_new_session():
    """Create a new conversation session."""
    session_id = str(uuid.uuid4())
    conversation_sessions[session_id] = []
    print(f"✅ Created new session: {session_id}")
    return SessionResponse(
        session_id=session_id,
        message="New conversation session created"
    )


@app.delete("/session/{session_id}", response_model=SessionResponse)
async def clear_session(session_id: str):
    """Clear a conversation session."""
    if session_id in conversation_sessions:
        del conversation_sessions[session_id]
        print(f"✅ Cleared session: {session_id}")
        return SessionResponse(
            session_id=session_id,
            message="Conversation session cleared"
        )
    else:
        raise HTTPException(status_code=404, detail="Session not found")


@app.get("/session/{session_id}/history")
async def get_session_history(session_id: str):
    """Get conversation history for a session."""
    if session_id in conversation_sessions:
        return {
            "session_id": session_id,
            "history": conversation_sessions[session_id],
            "message_count": len(conversation_sessions[session_id])
        }
    else:
        raise HTTPException(status_code=404, detail="Session not found")


@app.post("/extract-text", response_class=JSONResponse)
async def extract_hierarchical_json(file: UploadFile = File(...)):
    """
    Extract text from PDF and store in vector database.
    Processes legal documents with section/subsection structure.
    """
    try:
        contents = await file.read()
        pdf_doc = pymupdf.open(stream=contents, filetype="pdf")
        file_name = file.filename
        corpus = []
        current_section = None
        current_section_obj = None
        current_subsection_obj = None
        
        # Collect all subsections for batch storage
        all_subsections = []

        for page_num, page in enumerate(pdf_doc):
            lines = page.get_text("text").split("\n")
            for line in lines:
                line = line.strip()
                if not line or is_noise(line):
                    continue

                # Section + Subsection e.g., 1. (1)
                if SECTION_AND_SUBSECTION.match(line):
                    sec, subsec = SECTION_AND_SUBSECTION.match(line).groups()
                    if current_section != sec:
                        if current_section_obj:
                            current_section_obj["tags"] = list({tag for s in current_section_obj["subsections"] for tag in s["tags"]})
                            corpus.append(current_section_obj)
                        current_section = sec
                        current_section_obj = {"section": sec, "heading": None, "tags": [], "subsections": []}
                    
                    current_subsection_obj = {
                        "section": sec,
                        "number": subsec,
                        "content": line,
                        "tags": assign_tags(line),
                        "page": page_num + 1,
                        "file": file_name
                    }
                    current_section_obj["subsections"].append(current_subsection_obj)
                    all_subsections.append(current_subsection_obj)

                # Subsection only e.g., (1)
                elif SUBSECTION_PATTERN.match(line):
                    subsec = SUBSECTION_PATTERN.match(line).group(1)
                    current_subsection_obj = {
                        "section": current_section,
                        "number": subsec,
                        "content": line,
                        "tags": assign_tags(line),
                        "page": page_num + 1,
                        "file": file_name
                    }
                    if current_section_obj:
                        current_section_obj["subsections"].append(current_subsection_obj)
                        all_subsections.append(current_subsection_obj)

                # Continuation text
                else:
                    if current_subsection_obj:
                        current_subsection_obj["content"] += " " + line
                        current_subsection_obj["tags"].extend(assign_tags(line))
                        current_subsection_obj["tags"] = list(set(current_subsection_obj["tags"]))

        if current_section_obj:
            current_section_obj["tags"] = list({tag for s in current_section_obj["subsections"] for tag in s["tags"]})
            corpus.append(current_section_obj)

        # Store all subsections in Weaviate
        print(f"📦 Storing {len(all_subsections)} subsections in Weaviate...")
        batch_store_in_weaviate(all_subsections)
        print(f"✅ Successfully stored {len(all_subsections)} subsections")

        return JSONResponse(
            status_code=200,
            content={
                "message": f"Successfully processed {file_name}",
                "total_sections": len(corpus),
                "total_subsections": len(all_subsections),
                "data": corpus
            }
        )
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/query", response_model=QueryResponse)
async def query_legal_documents(request: QueryRequest):
    """
    Query the legal document database using Conversational RAG.
    
    This endpoint:
    1. Searches for relevant content in the vector database
    2. Uses conversation history if provided (via session_id or manual history)
    3. Uses Gemini to generate a contextual response
    4. Returns the answer with source citations
    5. Stores the Q&A in session history
    """
    try:
        if not request.query or len(request.query.strip()) == 0:
            raise HTTPException(status_code=400, detail="Query cannot be empty")
        
        print(f"\n{'='*60}")
        print(f"📝 New Query: {request.query}")
        
        # Determine conversation history
        conversation_history = None
        session_id = request.session_id
        
        if session_id and session_id in conversation_sessions:
            # Use session-based history
            conversation_history = conversation_sessions[session_id]
            print(f"💬 Using session {session_id} with {len(conversation_history)} previous messages")
        elif request.conversation_history:
            # Use manually provided history
            conversation_history = request.conversation_history
            print(f"💬 Using manual conversation history with {len(conversation_history)} messages")
        
        print(f"{'='*60}")
        
        # Process query using RAG with conversation context
        result = process_query(
            request.query, 
            top_k=request.top_k,
            conversation_history=conversation_history
        )
        
        # Store in session if session_id provided
        if session_id and session_id in conversation_sessions:
            conversation_sessions[session_id].append({
                "query": request.query,
                "answer": result["answer"]
            })
            # Keep only last 10 exchanges to avoid token limits
            if len(conversation_sessions[session_id]) > 10:
                conversation_sessions[session_id] = conversation_sessions[session_id][-10:]
            result["session_id"] = session_id
        
        return QueryResponse(**result)
        
    except Exception as e:
        print(f"❌ Error processing query: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing query: {str(e)}")


@app.get("/stats")
async def get_statistics():
    """Get statistics about the database and sessions."""
    try:
        count = get_object_count()
        return {
            "total_documents": count,
            "active_sessions": len(conversation_sessions),
            "status": "active"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    uvicorn.run("app.api.main:app", host="0.0.0.0", port=3000, reload=True)