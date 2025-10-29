# main.py
import uvicorn
from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import pymupdf
import re
from app.llm import ollama_client
from app.vector_store import store_in_weaviate, batch_store_in_weaviate

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Regex patterns
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

# Example tag keywords
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

def assign_tags(text: str):
    tags = []
    for keyword, taglist in TAG_KEYWORDS.items():
        if keyword.lower() in text.lower():
            tags.extend(taglist)
    return list(set(tags))

def is_noise(line: str):
    # existing noise patterns
    if any(noise in line for noise in NOISE_PATTERNS):
        return True
    # remove lines that are mostly underscores or dashes
    if re.fullmatch(r"[-_]{5,}", line.replace(" ", "")):
        return True
    # remove very short/empty lines
    if len(line.strip()) < 2:
        return True
    return False

@app.post("/extract-text", response_class=JSONResponse)
async def extract_hierarchical_json(file: UploadFile = File(...)):
    try:
        contents = await file.read()
        pdf_doc = pymupdf.open(stream=contents, filetype="pdf")
        file_name = file.filename
        corpus = []
        current_section = None
        current_section_obj = None
        current_subsection_obj = None
        
        # Collect all subsections to batch store at the end
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
                    current_section_obj["subsections"].append(current_subsection_obj)
                    all_subsections.append(current_subsection_obj)

                # Clauses / continuation - just append, don't store yet
                else:
                    if current_subsection_obj:
                        current_subsection_obj["content"] += " " + line
                        current_subsection_obj["tags"].extend(assign_tags(line))
                        current_subsection_obj["tags"] = list(set(current_subsection_obj["tags"]))

        if current_section_obj:
            current_section_obj["tags"] = list({tag for s in current_section_obj["subsections"] for tag in s["tags"]})
            corpus.append(current_section_obj)

        # 🚀 Store all subsections in Weaviate at once (batch operation)
        print(f"📦 Storing {len(all_subsections)} subsections in Weaviate...")
        batch_store_in_weaviate(all_subsections)
        print(f"✅ Successfully stored {len(all_subsections)} subsections")

        return JSONResponse(status_code=200, content={"data": corpus})
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return JSONResponse(status_code=500, content={"error": str(e)})


@app.get("/", response_class=JSONResponse)
def health_check():
    return JSONResponse(status_code=200, content={"message": "Service is up and running"})

if __name__ == "__main__":
    uvicorn.run("app.api.main:app", host="0.0.0.0", port=3000, reload=True)