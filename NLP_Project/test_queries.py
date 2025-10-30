"""
Test script to query the Legal RAG API
"""
import requests
import json

BASE_URL = "http://127.0.0.1:3000"

def test_health():
    """Test health endpoint"""
    print("\n" + "="*60)
    print("Testing Health Endpoint")
    print("="*60)
    
    response = requests.get(f"{BASE_URL}/")
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")

def test_stats():
    """Test statistics endpoint"""
    print("\n" + "="*60)
    print("Testing Statistics Endpoint")
    print("="*60)
    
    response = requests.get(f"{BASE_URL}/stats")
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")

def test_query(query: str, top_k: int = 5):
    """Test query endpoint"""
    print("\n" + "="*60)
    print(f"Testing Query: {query}")
    print("="*60)
    
    payload = {
        "query": query,
        "top_k": top_k
    }
    
    response = requests.post(f"{BASE_URL}/query", json=payload)
    
    if response.status_code == 200:
        result = response.json()
        print(f"\n📝 Query: {result['query']}")
        print(f"\n💡 Answer:\n{result['answer']}")
        print(f"\n📚 Number of Sources: {result['num_sources']}")
        print(f"\n📖 Sources:")
        for i, source in enumerate(result['sources'], 1):
            print(f"\n  [{i}] Section {source['section']}, Subsection {source['subsection']}")
            print(f"      File: {source['file']} (Page {source['page']})")
            print(f"      Preview: {source['content_preview'][:100]}...")
    else:
        print(f"❌ Error: {response.status_code}")
        print(f"Response: {response.text}")

if __name__ == "__main__":
    # Test health
    test_health()
    
    # Test stats
    test_stats()
    
    # Test queries
    test_queries = [
        "What is murder under BNS?",
        "What are the provisions for theft?",
        "Explain the rights of an arrested person",
        "What is the punishment for cybercrime?",
        "Tell me about juvenile justice provisions"
    ]
    
    for query in test_queries:
        test_query(query, top_k=3)
        print("\n" + "="*60 + "\n")
        input("Press Enter to continue to next query...")