import json
import chromadb

def init_vector_store(file_path: str = "data/products.json", db_path: str = "chroma_db"):
    """
    تقوم هذه الدالة بقراءة ملف المنتجات وإنشاء قاعدة بيانات متجهية (Vector DB).
    """
    # 1. قراءة بيانات المنتجات من ملف JSON
    with open(file_path, 'r', encoding='utf-8') as f:
        products = json.load(f)
        
    # 2. تهيئة اتصال بقاعدة بيانات ChromaDB لحفظ البيانات على القرص
    client = chromadb.PersistentClient(path=db_path)
    
    # 3. حذف الجدول القديم وإعادة إنشائه لضمان تطابق البيانات مع products.json
    # هذا يمنع بقاء منتجات قديمة محذوفة في قاعدة البيانات
    try:
        client.delete_collection(name="products")
    except Exception:
        pass
    collection = client.create_collection(name="products")
    
    # 4. تجهيز البيانات للإدخال
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
        
    # 5. إضافة البيانات للـ Collection
    collection.upsert(
        ids=ids,
        documents=documents,
        metadatas=metadatas
    )
    
    return collection

def search_products(query: str, collection, n_results: int = 3, max_distance: float = 1.5):
    """
    تقوم هذه الدالة بالبحث في ChromaDB عن المنتجات الأقرب لمعنى جملة العميل.
    
    Strict RAG: النتائج التي تتجاوز الـ max_distance يتم حذفها تلقائياً
    ChromaDB يستخدم L2 Distance: أقل = أقرب تطابقاً
    """
    # 1. البحث مع طلب المسافات (distances) لقياس جودة التطابق
    results = collection.query(
        query_texts=[query],
        n_results=n_results,
        include=["documents", "metadatas", "distances"]
    )
    
    # 2. تنسيق وفلترة النتائج بحسب جودة التطابق
    formatted_results = []
    
    if results["ids"] and len(results["ids"][0]) > 0:
        for i in range(len(results["ids"][0])):
            distance = results["distances"][0][i]
            
            # Strict Threshold: فقط النتائج القريبة فعلاً تمر
            if distance <= max_distance:
                formatted_results.append({
                    "id": results["ids"][0][i],
                    "document": results["documents"][0][i],
                    "metadata": results["metadatas"][0][i],
                    "distance": round(distance, 3)
                })
            
    return formatted_results

