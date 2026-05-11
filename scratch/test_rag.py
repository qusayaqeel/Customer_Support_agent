import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/..")

from core.rag import init_vector_store, search_products

def test_multilingual_rag():
    print("=== Testing Multilingual RAG ===")
    collection = init_vector_store(file_path="data/products.json", db_path="chroma_db")
    
    query = "لابتوب برمجة ويب 16 جيجا رام"
    print(f"\nSearching for: {query}")
    
    results = search_products(query, collection, n_results=2)
    
    if not results:
        print("No results found.")
    for res in results:
        print(f"[{res['distance']}] {res['metadata']['name']}")

if __name__ == "__main__":
    test_multilingual_rag()
