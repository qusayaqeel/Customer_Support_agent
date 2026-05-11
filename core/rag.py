import json
import chromadb

def init_vector_store(file_path: str = "data/products.json", db_path: str = "chroma_db_v2"):
    """
    تقوم هذه الدالة بقراءة ملف المنتجات وإنشاء قاعدة بيانات متجهية (Vector DB).
    """
    # 1. قراءة بيانات المنتجات من ملف JSON
    with open(file_path, 'r', encoding='utf-8') as f:
        products = json.load(f)
        
    # 2. تهيئة اتصال بقاعدة بيانات ChromaDB لحفظ البيانات على القرص
    client = chromadb.PersistentClient(path=db_path)
    
    # 2.5 تهيئة موديل متجهات متعدد اللغات (يدعم العربية بقوة)
    from chromadb.utils import embedding_functions
    sentence_transformer_ef = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
    
    # 3. محاولة الحصول على الـ Collection أو إنشاءه
    collection = client.get_or_create_collection(name="products", embedding_function=sentence_transformer_ef)
    
    # 4. التحقق إذا كان الـ Collection يحتوي على بيانات
    if collection.count() == 0:
        print("Ingesting products into ChromaDB for the first time...")
        # تجهيز البيانات للإدخال
        ids = []
        documents = []
        metadatas = []
        
        for p in products:
            ids.append(str(p["id"])) # يجب أن يكون الـ ID نص (String)
            
            # النص الذي سيقوم ChromaDB بتحويله لمتجهات (Embeddings) للبحث فيه
            doc = f"{p['name']} - {p['description']} - السعر: {p['price_ils']} شيكل"
            documents.append(doc)
            
            # معلومات إضافية (Metadata) - بدون stock لأنه معلومة داخلية
            metadatas.append({
                "category": p["category"],
                "price": p["price_ils"],
                "name": p["name"]
            })
            
        # إضافة البيانات للـ Collection
        collection.upsert(
            ids=ids,
            documents=documents,
            metadatas=metadatas
        )
    
    return collection

def search_products(query: str, collection, n_results: int = 5, max_distance: float = 1.2, max_price: int = None):
    """
    تقوم هذه الدالة بالبحث في ChromaDB عن المنتجات الأقرب لمعنى جملة العميل.
    
    Strict RAG: النتائج التي تتجاوز الـ max_distance يتم حذفها تلقائياً
    ChromaDB يستخدم L2 Distance: أقل = أقرب تطابقاً
    """
    # 1. البحث مع طلب المسافات (distances) لقياس جودة التطابق
    where_clause = None
    if max_price is not None:
        where_clause = {"price": {"$lte": max_price}}
        
    results = collection.query(
        query_texts=[query],
        n_results=n_results,
        where=where_clause,
        include=["documents", "metadatas", "distances"]
    )
    
    # 2. تنسيق وفلترة النتائج بحسب جودة التطابق
    formatted_results = []
    seen_ids = set()
    
    if results["ids"] and len(results["ids"][0]) > 0:
        for i in range(len(results["ids"][0])):
            distance = results["distances"][0][i]
            p_id = results["ids"][0][i]
            
            # Strict Threshold: فقط النتائج القريبة فعلاً تمر
            if distance <= max_distance:
                formatted_results.append({
                    "id": p_id,
                    "document": results["documents"][0][i],
                    "metadata": results["metadatas"][0][i],
                    "distance": round(distance, 3)
                })
                seen_ids.add(p_id)
                
    # 3. Keyword Match Fallback (Hybrid Search)
    # الموديل أحياناً يفشل في ربط الجمع (لابتوبات) بالمفرد (لابتوب)
    # سنقوم ببحث نصي بسيط إذا كان الاستعلام قصيراً لتعويض ضعف الـ Embeddings
    import json
    try:
        with open("data/products.json", "r", encoding="utf-8") as f:
            all_products = json.load(f)
            
        # تنظيف مبسط للكلمة (إزالة جمع المؤنث السالم لابتوبات -> لابتوب)
        base_query = query.replace("ات", "")
        if len(base_query) < 3:
            base_query = query
            
        for p in all_products:
            if p["id"] not in seen_ids:
                if (max_price is None or p["price_ils"] <= max_price):
                    if base_query in p["name"] or base_query in p["category"] or query in p["name"] or query in p["category"]:
                        formatted_results.append({
                            "id": str(p["id"]),
                            "document": f"{p['name']} - {p['description']} - السعر: {p['price_ils']} شيكل",
                            "metadata": {"name": p["name"], "price": p["price_ils"], "category": p["category"]},
                            "distance": 0.0 # تطابق تام
                        })
                        seen_ids.add(p["id"])
    except Exception as e:
        pass
        
    # فرز النتائج بحيث يظهر التطابق التام (distance=0.0) أولاً
    formatted_results.sort(key=lambda x: x["distance"])
    
    return formatted_results[:n_results]

