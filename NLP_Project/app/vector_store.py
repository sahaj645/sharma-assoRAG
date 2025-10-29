# vector.py
import os
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
import weaviate
from weaviate.auth import AuthApiKey
from typing import List

load_dotenv()

# Load embedding model
embedding_model = SentenceTransformer("all-MiniLM-L6-v2")

# Weaviate configuration
WEAVIATE_URL = "https://s96hz7wsskjotuoto9vcg.c0.asia-southeast1.gcp.weaviate.cloud"
WEAVIATE_API_KEY = "ODhpcjJiWFZLd1NrUjR5c196YWZtQW9vUC94V0V3QUNCT2NUckluRmV6TUF4U0U5TnczQ0dNbkZuMXE0PV92MjAw"

# Initialize v3 client (correct syntax)
client = weaviate.Client(
    url=WEAVIATE_URL,
    auth_client_secret=AuthApiKey(api_key=WEAVIATE_API_KEY),
    timeout_config=(5, 30)  # Increased timeout for batch operations
)

CLASS_NAME = "LegalText"

# Ensure schema exists
def init_schema():
    """Initialize Weaviate schema if it doesn't exist."""
    try:
        # Check if class exists
        schema = client.schema.get()
        class_names = [c["class"] for c in schema.get("classes", [])]
        
        if CLASS_NAME not in class_names:
            schema_class = {
                "class": CLASS_NAME,
                "description": "Extracted legal text segments",
                "vectorizer": "none",  # We're providing our own vectors
                "properties": [
                    {"name": "section", "dataType": ["string"]},
                    {"name": "subsection", "dataType": ["string"]},
                    {"name": "content", "dataType": ["text"]},
                    {"name": "tags", "dataType": ["string[]"]},
                    {"name": "page", "dataType": ["int"]},
                    {"name": "file", "dataType": ["string"]}
                ]
            }
            client.schema.create_class(schema_class)
            print(f"✅ Created schema class: {CLASS_NAME}")
        else:
            print(f"✅ Schema class {CLASS_NAME} already exists")
    except Exception as e:
        print(f"❌ Error initializing schema: {e}")
        raise

# Initialize schema on import
init_schema()

def embed_text(text: str):
    """Convert text to vector embeddings."""
    return embedding_model.encode(text).tolist()

def embed_batch(texts: List[str]):
    """Convert multiple texts to vector embeddings efficiently."""
    return embedding_model.encode(texts).tolist()

def store_in_weaviate(subsection_obj: dict):
    """Store a single text object in Weaviate with vector embeddings."""
    try:
        vector = embed_text(subsection_obj["content"])
        
        # Prepare data object
        data_object = {
            "section": str(subsection_obj.get("section", "")),
            "subsection": str(subsection_obj.get("number", "")),
            "content": subsection_obj.get("content", ""),
            "tags": subsection_obj.get("tags", []),
            "page": int(subsection_obj.get("page", 0)),
            "file": subsection_obj.get("file", ""),
        }
        
        # Create object with vector
        uuid = client.data_object.create(
            data_object=data_object,
            class_name=CLASS_NAME,
            vector=vector
        )
        
        print(f"✅ Stored: Section {subsection_obj.get('section')}({subsection_obj.get('number')}) - UUID: {uuid}")
        return uuid
        
    except Exception as e:
        print(f"❌ Error storing in Weaviate: {e}")
        raise

def batch_store_in_weaviate(subsection_objects: List[dict]):
    """Store multiple text objects in Weaviate efficiently using batch operations."""
    try:
        if not subsection_objects:
            print("⚠️ No subsections to store")
            return
        
        # Extract all content for batch embedding
        contents = [obj["content"] for obj in subsection_objects]
        print(f"🔄 Generating embeddings for {len(contents)} documents...")
        vectors = embed_batch(contents)
        
        # Configure batch
        client.batch.configure(
            batch_size=100,
            dynamic=True,
            timeout_retries=3,
        )
        
        print(f"🔄 Uploading {len(subsection_objects)} documents to Weaviate...")
        
        with client.batch as batch:
            for i, (subsection_obj, vector) in enumerate(zip(subsection_objects, vectors)):
                data_object = {
                    "section": str(subsection_obj.get("section", "")),
                    "subsection": str(subsection_obj.get("number", "")),
                    "content": subsection_obj.get("content", ""),
                    "tags": subsection_obj.get("tags", []),
                    "page": int(subsection_obj.get("page", 0)),
                    "file": subsection_obj.get("file", ""),
                }
                
                batch.add_data_object(
                    data_object=data_object,
                    class_name=CLASS_NAME,
                    vector=vector
                )
                
                # Progress indicator
                if (i + 1) % 50 == 0:
                    print(f"  📤 Processed {i + 1}/{len(subsection_objects)} documents...")
        
        print(f"✅ Successfully stored {len(subsection_objects)} documents in Weaviate!")
        
    except Exception as e:
        print(f"❌ Error in batch storage: {e}")
        raise

def search_similar(query: str, limit: int = 5):
    """Search for similar legal texts using vector similarity."""
    try:
        query_vector = embed_text(query)
        
        result = (
            client.query
            .get(CLASS_NAME, ["section", "subsection", "content", "tags", "page", "file"])
            .with_near_vector({"vector": query_vector})
            .with_limit(limit)
            .with_additional(["distance"])  # Include similarity score
            .do()
        )
        
        return result.get("data", {}).get("Get", {}).get(CLASS_NAME, [])
    except Exception as e:
        print(f"❌ Error searching Weaviate: {e}")
        return []

def get_object_count():
    """Get the total number of objects stored in Weaviate."""
    try:
        result = client.query.aggregate(CLASS_NAME).with_meta_count().do()
        count = result.get("data", {}).get("Aggregate", {}).get(CLASS_NAME, [{}])[0].get("meta", {}).get("count", 0)
        return count
    except Exception as e:
        print(f"❌ Error getting count: {e}")
        return 0