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
    استخدم هذه الأداة للبحث عن المنتجات في المتجر بناءً على طلب المستخدم. (مثل: لابتوب، ايفون، ساعات).
    
    Args:
        query: كلمة البحث (مثال: لابتوب ديل، ايفون 15)
    """
    # تهيئة الاتصال بقاعدة المتجهات والبحث فيها
    collection = init_vector_store(file_path=PRODUCTS_FILE, db_path=CHROMA_DB_PATH)
    results = search_products(query, collection)
    return str(results)

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
