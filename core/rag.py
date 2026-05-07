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
    
    # 3. إنشاء أو جلب جدول (Collection) للمنتجات
    collection = client.get_or_create_collection(name="products")
    
    # 4. تجهيز البيانات للإدخال
    ids = []
    documents = []
    metadatas = []
    
    for p in products:
        ids.append(str(p["id"])) # يجب أن يكون الـ ID نص (String)
        
        # النص الذي سيقوم ChromaDB بتحويله لمتجهات (Embeddings) للبحث فيه
        doc = f"{p['name']} - {p['description']} - السعر: {p['price_ils']} شيكل"
        documents.append(doc)
        
        # معلومات إضافية (Metadata) يمكن الفلترة بناءً عليها لاحقاً
        metadatas.append({
            "category": p["category"],
            "price": p["price_ils"],
            "stock": p["stock"],
            "name": p["name"]
        })
        
    # 5. إضافة البيانات للـ Collection
    collection.upsert(
        ids=ids,
        documents=documents,
        metadatas=metadatas
    )
    
    return collection

def search_products(query: str, collection, n_results: int = 3):
    """
    تقوم هذه الدالة بالبحث في ChromaDB عن المنتجات الأقرب لمعنى جملة العميل.
    """
    # 1. استدعاء دالة البحث المدمجة في ChromaDB
    # الدالة بتاخذ النص (query_texts)، بتحوله لمتجهات، وبترجع أقرب نتائج
    results = collection.query(
        query_texts=[query],
        n_results=n_results
    )
    
    # 2. تنسيق النتائج (Formatting)
    # ChromaDB بترجع البيانات معقدة شوي (قوائم داخل قوائم)، فاحنا بنرتبها لتكون سهلة الاستخدام
    formatted_results = []
    
    # التأكد إنه في نتائج رجعت
    if results["ids"] and len(results["ids"][0]) > 0:
        for i in range(len(results["ids"][0])):
            formatted_results.append({
                "id": results["ids"][0][i],
                "document": results["documents"][0][i],
                "metadata": results["metadatas"][0][i]
            })
            
    return formatted_results
