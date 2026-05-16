import json
import chromadb

def init_vector_store(file_path: str = "data/products.json", db_path: str = "chroma_db"):
    """
    Reads the products file and creates/loads a vector database (ChromaDB).
    Uses a multilingual sentence transformer model for Arabic support.
    """
    # 1. Read product data from JSON file
    with open(file_path, 'r', encoding='utf-8') as f:
        products = json.load(f)
        
    # 2. Initialize ChromaDB persistent client for disk storage
    client = chromadb.PersistentClient(path=db_path)
    
    # 3. Initialize multilingual embedding model (strong Arabic support)
    from chromadb.utils import embedding_functions
    sentence_transformer_ef = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
    
    # 4. Get or create the collection
    collection = client.get_or_create_collection(name="products", embedding_function=sentence_transformer_ef)
    
    # 5. Check if collection needs data ingestion
    if collection.count() == 0:
        print("Ingesting products into ChromaDB for the first time...")
        ids = []
        documents = []
        metadatas = []
        
        for p in products:
            ids.append(str(p["id"]))
            
            # Text that ChromaDB will convert to embeddings for semantic search
            doc = f"{p['name']} - {p['description']} - السعر: {p['price_ils']} شيكل"
            documents.append(doc)
            
            # Metadata (stock excluded - internal info only)
            metadatas.append({
                "category": p["category"],
                "price": p["price_ils"],
                "name": p["name"],
                "image": p.get("image", "")
            })
            
        # Upsert data into the collection
        collection.upsert(
            ids=ids,
            documents=documents,
            metadatas=metadatas
        )
    
    return collection

def search_products(query: str, collection, n_results: int = 5, max_distance: float = 1.2, max_price: int = None):
    """
    Searches ChromaDB for products closest in meaning to the customer's query.
    
    Strict RAG: Results exceeding max_distance are automatically filtered out.
    ChromaDB uses L2 Distance: lower = closer match.
    """
    # 1. Query with distances for match quality measurement
    where_clause = None
    if max_price is not None:
        where_clause = {"price": {"$lte": max_price}}
        
    results = collection.query(
        query_texts=[query],
        n_results=n_results,
        where=where_clause,
        include=["documents", "metadatas", "distances"]
    )
    
    # 2. Format and filter results by match quality
    formatted_results = []
    seen_ids = set()
    
    if results["ids"] and len(results["ids"][0]) > 0:
        for i in range(len(results["ids"][0])):
            distance = results["distances"][0][i]
            p_id = results["ids"][0][i]
            
            # Strict Threshold: only truly close matches pass
            if distance <= max_distance:
                formatted_results.append({
                    "id": p_id,
                    "document": results["documents"][0][i],
                    "metadata": results["metadatas"][0][i],
                    "distance": round(distance, 3)
                })
                seen_ids.add(p_id)
                
    # 3. Keyword Match Fallback (Hybrid Search)
    # Embedding models sometimes fail to link plural forms (e.g., لابتوبات → لابتوب)
    # Simple text search compensates for embedding weaknesses on short queries
    import json
    try:
        with open("data/products.json", "r", encoding="utf-8") as f:
            all_products = json.load(f)
            
        # Basic stemming: remove feminine plural suffix (لابتوبات → لابتوب)
        base_query = query.replace("ات", "")
        if "تلفون" in query or "هاتف" in query or "تليفون" in query or "موبايل" in query or "جوال" in query:
            base_query = "جوال"
            query = "الهواتف الذكية"
            
        if len(base_query) < 3:
            base_query = query
            
        for p in all_products:
            if p["id"] not in seen_ids:
                if (max_price is None or p["price_ils"] <= max_price):
                    if base_query in p["name"] or base_query in p["category"] or query in p["name"] or query in p["category"]:
                        formatted_results.append({
                            "id": str(p["id"]),
                            "document": f"{p['name']} - {p['description']} - السعر: {p['price_ils']} شيكل",
                            "metadata": {"name": p["name"], "price": p["price_ils"], "category": p["category"], "image": p.get("image", "")},
                            "distance": 0.0  # Exact keyword match
                        })
                        seen_ids.add(p["id"])
    except Exception as e:
        pass
        
    # Sort results: exact matches (distance=0.0) first
    formatted_results.sort(key=lambda x: x["distance"])
    
    return formatted_results[:n_results]
