







"""
RAG (Retrieval-Augmented Generation) Module with Conversational Context
Handles query processing and response generation with conversation history
"""
from typing import List, Dict
from app.vector_store import search_similar
from app.llm import generate_response_with_context, generate_conversational_response


def format_context(search_results: List[Dict]) -> str:
    """
    Format search results into a readable context string for the LLM.
    
    Args:
        search_results: List of search results from Weaviate
        
    Returns:
        Formatted context string
    """
    if not search_results:
        return "No relevant information found in the database."
    
    context_parts = []
    for i, result in enumerate(search_results, 1):
        section = result.get('section', 'N/A')
        subsection = result.get('subsection', 'N/A')
        content = result.get('content', '')
        file_name = result.get('file', 'Unknown')
        page = result.get('page', 'N/A')
        
        # Get similarity score if available
        additional = result.get('_additional', {})
        distance = additional.get('distance', 'N/A')
        
        context_part = f"""
[Reference {i}]
Source: {file_name} (Page {page})
Section: {section}, Subsection: {subsection}
Relevance Score: {1 - float(distance) if distance != 'N/A' else 'N/A'}
Content: {content}
---
"""
        context_parts.append(context_part)
    
    return "\n".join(context_parts)


def format_conversation_history(conversation_history: List[Dict]) -> str:
    """
    Format conversation history for the LLM.
    
    Args:
        conversation_history: List of previous Q&A pairs
        
    Returns:
        Formatted conversation history string
    """
    if not conversation_history:
        return ""
    
    history_parts = []
    for i, exchange in enumerate(conversation_history, 1):
        history_part = f"""
Previous Question {i}: {exchange.get('query', '')}
Previous Answer {i}: {exchange.get('answer', '')}
"""
        history_parts.append(history_part)
    
    return "\n".join(history_parts)


def process_query(query: str, top_k: int = 5, conversation_history: List[Dict] = None) -> Dict:
    """
    Process a user query using RAG approach with optional conversation history.
    
    Steps:
    1. Search for similar content in vector database
    2. Format the retrieved context
    3. Include conversation history if available
    4. Generate response using Gemini with the context
    
    Args:
        query: User's question
        top_k: Number of similar documents to retrieve
        conversation_history: List of previous Q&A pairs (optional)
        
    Returns:
        Dictionary containing response and metadata
    """
    try:
        # Step 1: Retrieve similar documents from vector database
        print(f"🔍 Searching for relevant documents for query: '{query}'")
        search_results = search_similar(query, limit=top_k)
        
        if not search_results:
            return {
                "query": query,
                "answer": "I couldn't find any relevant information in the legal database to answer your question. Please try rephrasing your query or ask about specific sections of BNS, BNSS, or BSA.",
                "sources": [],
                "context_used": False,
                "conversation_aware": bool(conversation_history)
            }
        
        print(f"✅ Found {len(search_results)} relevant documents")
        
        # Step 2: Format context for LLM
        formatted_context = format_context(search_results)
        
        # Step 3: Check if this is a conversational query
        if conversation_history and len(conversation_history) > 0:
            print(f"💬 Using conversation history ({len(conversation_history)} previous exchanges)")
            formatted_history = format_conversation_history(conversation_history)
            response = generate_conversational_response(query, formatted_context, formatted_history)
        else:
            print("🤖 Generating response with Gemini...")
            response = generate_response_with_context(query, formatted_context)
        
        # Step 4: Extract source references
        sources = []
        for result in search_results:
            sources.append({
                "section": result.get('section', 'N/A'),
                "subsection": result.get('subsection', 'N/A'),
                "file": result.get('file', 'Unknown'),
                "page": result.get('page', 'N/A'),
                "content_preview": result.get('content', '')[:200] + "..."
            })
        
        print("✅ Response generated successfully")
        
        return {
            "query": query,
            "answer": response,
            "sources": sources,
            "context_used": True,
            "num_sources": len(sources),
            "conversation_aware": bool(conversation_history)
        }
        
    except Exception as e:
        print(f"❌ Error processing query: {e}")
        return {
            "query": query,
            "answer": f"An error occurred while processing your query: {str(e)}",
            "sources": [],
            "context_used": False,
            "error": str(e),
            "conversation_aware": False
        }