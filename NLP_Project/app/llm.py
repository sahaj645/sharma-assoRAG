# """
# LLM Module - Google Gemini Integration
# Handles all interactions with Gemini API for response generation
# """
# import os
# from dotenv import load_dotenv
# import google.generativeai as genai
# from typing import Optional

# load_dotenv()

# # Configure Gemini API
# GEMINI_API_KEY = "AIzaSyA2ZBwueKr2v5LWlurG9Ncao0daS7P6kLs"

# if not GEMINI_API_KEY:
#     raise ValueError("GEMINI_API_KEY not found in environment variables. Please add it to .env file")

# genai.configure(api_key=GEMINI_API_KEY)

# # Initialize Gemini model - Using the correct model name for your API key
# # Using gemini-2.5-flash-preview-05-20 (verified working model)
# try:
#     model = genai.GenerativeModel('gemini-2.5-flash-preview-05-20')
#     print("✅ Using Gemini 2.5 Flash Preview model")
# except Exception as e:
#     print(f"❌ Failed to load model: {e}")
#     raise

# # System prompt for legal assistant
# SYSTEM_PROMPT = """You are an expert legal assistant specializing in Indian law, specifically the Bharatiya Nyaya Sanhita (BNS), Bharatiya Nagarik Suraksha Sanhita (BNSS), and Bharatiya Sakshya Adhiniyam (BSA).

# Your role is to:
# 1. Provide accurate, clear, and helpful answers based on the legal documents provided
# 2. Cite specific sections and subsections when answering
# 3. Explain legal concepts in simple terms when needed
# 4. Always maintain objectivity and accuracy
# 5. If the context doesn't contain enough information, clearly state that

# Guidelines:
# - Be concise but comprehensive
# - Use proper legal terminology but explain complex terms
# - Always reference the source sections you're citing from
# - If asked about something not in the provided context, say so clearly
# - Maintain a professional and helpful tone
# """


# def generate_response_with_context(query: str, context: str) -> str:
#     """
#     Generate a response using Gemini with the provided context.
    
#     Args:
#         query: User's question
#         context: Retrieved context from vector database
        
#     Returns:
#         Generated response string
#     """
#     try:
#         # Construct the prompt with system instructions, context, and query
#         full_prompt = f"""{SYSTEM_PROMPT}

# RETRIEVED CONTEXT FROM LEGAL DOCUMENTS:
# {context}

# USER QUESTION:
# {query}

# Please provide a comprehensive answer based on the context above. Make sure to:
# 1. Reference specific sections and subsections
# 2. Explain the legal provisions clearly
# 3. Use examples if it helps understanding
# 4. Be accurate and cite your sources from the context

# ANSWER:"""

#         # Generate response using Gemini
#         response = model.generate_content(
#             full_prompt,
#             generation_config=genai.types.GenerationConfig(
#                 temperature=0.3,  # Lower temperature for more factual responses
#                 max_output_tokens=2048,
#             )
#         )
        
#         return response.text
        
#     except Exception as e:
#         print(f"❌ Error generating response with Gemini: {e}")
#         return f"I encountered an error while generating the response: {str(e)}"


# def generate_simple_response(query: str) -> str:
#     """
#     Generate a simple response without context (fallback).
    
#     Args:
#         query: User's question
        
#     Returns:
#         Generated response string
#     """
#     try:
#         prompt = f"""{SYSTEM_PROMPT}

# USER QUESTION:
# {query}

# Note: No specific context was found in the database. Please provide a general response or ask the user to rephrase their question.

# ANSWER:"""

#         response = model.generate_content(
#             prompt,
#             generation_config=genai.types.GenerationConfig(
#                 temperature=0.3,
#                 max_output_tokens=1024,
#             )
#         )
#         return response.text
        
#     except Exception as e:
#         print(f"❌ Error generating simple response: {e}")
#         return f"I encountered an error: {str(e)}"


# def check_api_connection() -> bool:
#     """
#     Check if Gemini API is properly configured and accessible.
    
#     Returns:
#         True if API is accessible, False otherwise
#     """
#     try:
#         # Try a simple generation to test the connection
#         test_response = model.generate_content("Say hello")
#         return bool(test_response.text)
#     except Exception as e:
#         print(f"❌ Gemini API connection failed: {e}")
#         return False


# def list_available_models():
#     """
#     List all available Gemini models (for debugging).
#     """
#     try:
#         print("\n📋 Available Gemini Models:")
#         for m in genai.list_models():
#             if 'generateContent' in m.supported_generation_methods:
#                 print(f"  - {m.name}")
#     except Exception as e:
#         print(f"❌ Error listing models: {e}")

















"""
LLM Module - Google Gemini Integration with Conversational Support
Handles all interactions with Gemini API for response generation
"""
import os
from dotenv import load_dotenv
import google.generativeai as genai
from typing import Optional

load_dotenv()

# Configure Gemini API
GEMINI_API_KEY = "AIzaSyA2ZBwueKr2v5LWlurG9Ncao0daS7P6kLs"

if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY not found in environment variables. Please add it to .env file")

genai.configure(api_key=GEMINI_API_KEY)

# Initialize Gemini model
try:
    model = genai.GenerativeModel('gemini-2.5-flash-preview-05-20')
    print("✅ Using Gemini 2.5 Flash Preview model")
except Exception as e:
    print(f"❌ Failed to load model: {e}")
    raise

# System prompt for legal assistant
SYSTEM_PROMPT = """You are an expert legal assistant specializing in Indian law, specifically the Bharatiya Nyaya Sanhita (BNS), Bharatiya Nagarik Suraksha Sanhita (BNSS), and Bharatiya Sakshya Adhiniyam (BSA).

Your role is to:
1. Provide accurate, clear, and helpful answers based on the legal documents provided
2. Cite specific sections and subsections when answering
3. Explain legal concepts in simple terms when needed
4. Always maintain objectivity and accuracy
5. If the context doesn't contain enough information, clearly state that
6. When responding to follow-up questions, refer to previous conversation context

Guidelines:
- Be concise but comprehensive
- Use proper legal terminology but explain complex terms
- Always reference the source sections you're citing from
- If asked about something not in the provided context, say so clearly
- Maintain a professional and helpful tone
- For follow-up questions, acknowledge what was discussed before
"""


def generate_response_with_context(query: str, context: str) -> str:
    """
    Generate a response using Gemini with the provided context.
    
    Args:
        query: User's question
        context: Retrieved context from vector database
        
    Returns:
        Generated response string
    """
    try:
        # Construct the prompt with system instructions, context, and query
        full_prompt = f"""{SYSTEM_PROMPT}

RETRIEVED CONTEXT FROM LEGAL DOCUMENTS:
{context}

USER QUESTION:
{query}

Please provide a comprehensive answer based on the context above. Make sure to:
1. Reference specific sections and subsections
2. Explain the legal provisions clearly
3. Use examples if it helps understanding
4. Be accurate and cite your sources from the context

ANSWER:"""

        # Generate response using Gemini
        response = model.generate_content(
            full_prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.3,  # Lower temperature for more factual responses
                max_output_tokens=2048,
            )
        )
        
        return response.text
        
    except Exception as e:
        print(f"❌ Error generating response with Gemini: {e}")
        return f"I encountered an error while generating the response: {str(e)}"


def generate_conversational_response(query: str, context: str, conversation_history: str) -> str:
    """
    Generate a conversational response using Gemini with context and conversation history.
    
    Args:
        query: User's current question
        context: Retrieved context from vector database
        conversation_history: Formatted previous conversation
        
    Returns:
        Generated response string
    """
    try:
        # Construct the prompt with conversation history
        full_prompt = f"""{SYSTEM_PROMPT}

PREVIOUS CONVERSATION:
{conversation_history}

RETRIEVED CONTEXT FROM LEGAL DOCUMENTS (for current question):
{context}

CURRENT USER QUESTION:
{query}

Please provide a comprehensive answer based on:
1. The current context retrieved from legal documents
2. The previous conversation (if the question is a follow-up)
3. Reference specific sections and subsections
4. If this is a follow-up question, acknowledge what was discussed before
5. Be accurate and cite your sources

ANSWER:"""

        # Generate response using Gemini
        response = model.generate_content(
            full_prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.4,  # Slightly higher for conversational responses
                max_output_tokens=2048,
            )
        )
        
        return response.text
        
    except Exception as e:
        print(f"❌ Error generating conversational response: {e}")
        return f"I encountered an error while generating the response: {str(e)}"


def generate_simple_response(query: str) -> str:
    """
    Generate a simple response without context (fallback).
    
    Args:
        query: User's question
        
    Returns:
        Generated response string
    """
    try:
        prompt = f"""{SYSTEM_PROMPT}

USER QUESTION:
{query}

Note: No specific context was found in the database. Please provide a general response or ask the user to rephrase their question.

ANSWER:"""

        response = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.3,
                max_output_tokens=1024,
            )
        )
        return response.text
        
    except Exception as e:
        print(f"❌ Error generating simple response: {e}")
        return f"I encountered an error: {str(e)}"


def check_api_connection() -> bool:
    """
    Check if Gemini API is properly configured and accessible.
    
    Returns:
        True if API is accessible, False otherwise
    """
    try:
        # Try a simple generation to test the connection
        test_response = model.generate_content("Say hello")
        return bool(test_response.text)
    except Exception as e:
        print(f"❌ Gemini API connection failed: {e}")
        return False


def list_available_models():
    """
    List all available Gemini models (for debugging).
    """
    try:
        print("\n📋 Available Gemini Models:")
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                print(f"  - {m.name}")
    except Exception as e:
        print(f"❌ Error listing models: {e}")