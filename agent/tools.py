from langchain_core.tools import tool
from core.rag import init_vector_store, search_products
from db.database import save_order

# إعدادات مسارات قواعد البيانات الثابتة لتسهيل الوصول إليها داخل الأدوات
CHROMA_DB_PATH = "chroma_db"
PRODUCTS_FILE = "data/products.json"
SQLITE_DB_PATH = "orders.db"

@tool
def search_store_products(query: str) -> str:
    """
    استخدم هذه الأداة للبحث عن المنتجات في المتجر بناءً على طلب المستخدم.
    
    Args:
        query: كلمة البحث (مثال: لابتوب ديل، ايفون 15)
    """
    collection = init_vector_store(file_path=PRODUCTS_FILE, db_path=CHROMA_DB_PATH)
    results = search_products(query, collection)
    
    # تنسيق النتائج برمجياً - هنا نتحكم بالضبط بما يراه الموديل
    # لا نرسل الـ stock ولا الـ metadata الخام
    if not results:
        return "لا توجد نتائج مطابقة للبحث"
    
    formatted_lines = []
    for item in results:
        product_id = item["id"]
        name = item["metadata"]["name"]
        price = item["metadata"]["price"]
        description = item["document"].split(" - ")[1] if " - " in item["document"] else ""
        formatted_lines.append(f"المنتج: {name} | الكود: {product_id} | السعر: {price} شيكل | الوصف: {description}")
    
    return "\n".join(formatted_lines)

@tool
def save_customer_order(product_id: str, customer_name: str, customer_phone: str) -> str:
    """
    استخدم هذه الأداة لحفظ طلب العميل عندما يؤكد رغبته في شراء منتج محدد. يجب أن تطلب اسمه ورقم هاتفه أولاً.
    
    Args:
        product_id: معرف المنتج (ID) الذي يريد العميل شراءه.
        customer_name: اسم العميل
        customer_phone: رقم هاتف العميل
    """
    # محاولة حفظ الطلب في قاعدة بيانات SQLite
    success = save_order(product_id, customer_name, customer_phone, db_path=SQLITE_DB_PATH)
    if success:
        return "تم حفظ الطلب بنجاح في قاعدة البيانات."
    else:
        return "حدث خطأ أثناء محاولة حفظ الطلب في قاعدة البيانات."

# نقوم بتجميع الأدوات في قائمة (List) لتمريرها لاحقاً لدالة bind_tools()
tools = [search_store_products, save_customer_order]
