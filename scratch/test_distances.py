import os
from core.rag import init_vector_store
from agent.tools import PRODUCTS_FILE, CHROMA_DB_PATH

collection = init_vector_store(PRODUCTS_FILE, CHROMA_DB_PATH)
results = collection.query(
    query_texts=["لابتوبات"],
    n_results=10,
    include=["documents", "metadatas", "distances"]
)

print("Results for 'لابتوبات':")
for i in range(len(results["ids"][0])):
    print(f"Distance: {results['distances'][0][i]:.3f} | Name: {results['metadatas'][0][i]['name']}")

results = collection.query(
    query_texts=["لابتوب"],
    n_results=10,
    include=["documents", "metadatas", "distances"]
)

print("\nResults for 'لابتوب':")
for i in range(len(results["ids"][0])):
    print(f"Distance: {results['distances'][0][i]:.3f} | Name: {results['metadatas'][0][i]['name']}")
