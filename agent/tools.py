from typing import Optional, Union
from langchain_core.tools import tool
from core.rag import init_vector_store, search_products
from db.database import save_order

# إعدادات مسارات قواعد البيانات الثابتة لتسهيل الوصول إليها داخل الأدوات
CHROMA_DB_PATH = "chroma_db_v2"
PRODUCTS_FILE = "data/products.json"
SQLITE_DB_PATH = "orders.db"

@tool
def search_store_products(query: str, max_price: Union[int, str, None] = None) -> str:
    """
    استخدم هذه الأداة للبحث عن المنتجات في المتجر بناءً على طلب المستخدم.
    
    Args:
       يجب تمرير الكلمات المفتاحية باللغة العربية بوضوح.
    يمكن تمرير الحد الأقصى للسعر (max_price) إذا ذكره المستخدم لتصفية النتائج.
    """
    import json
    from core.rag import init_vector_store, search_products
    
    if isinstance(max_price, str):
        try:
            max_price = int(max_price)
        except ValueError:
            max_price = None
            
    # تنظيف الكلمة المفتاحية
    cleaned_query = query.strip()
    if not cleaned_query or len(cleaned_query) < 2:
        return "لا توجد نتائج مطابقة للبحث يرجى تحديد المنتج المطلوب بشكل اوضح"
    
    # تنظيف أحرف خطيرة (حماية إضافية)
    cleaned_query = cleaned_query.replace(";", "").replace("--", "").replace("DROP", "").replace("DELETE", "").replace("UPDATE", "")
    
    collection = init_vector_store(file_path=PRODUCTS_FILE, db_path=CHROMA_DB_PATH)
    results = search_products(cleaned_query, collection, max_price=max_price)
    
    # تنسيق النتائج برمجياً - هنا نتحكم بالضبط بما يراه الموديل
    # لا نرسل الـ stock ولا الـ metadata الخام
    if not results:
        return "لا توجد نتائج مطابقة للبحث. لا تخترع منتجات. أخبر العميل أنه غير متوفر حالياً ويمكنك أن تقترح أن نطلب له طلبية خاصة."
    
    formatted_lines = ["[نتائج البحث - هذه هي المنتجات المتوفرة فقط. لا تذكر أي منتج آخر غير المذكور هنا]:"]
    for item in results:
        product_id = item["id"]
        name = item["metadata"]["name"]
        price = item["metadata"]["price"]
        description = item["document"].split(" - ")[1] if " - " in item["document"] else ""
        formatted_lines.append(f"المنتج: {name} | الكود: {product_id} | السعر: {price} شيكل | الوصف: {description}")
    
    formatted_lines.append("[انتهت النتائج - لا تضف أي منتجات أخرى من معرفتك]")
    return "\n".join(formatted_lines)

@tool
def save_customer_order(product_id: str, customer_name: str, customer_phone: str, city: str = "", address: str = "", payment_method: str = "") -> str:
    """
    استخدم هذه الأداة لحفظ طلب العميل عندما يؤكد رغبته في شراء منتج محدد. يجب أن تطلب اسمه ورقم هاتفه أولاً.
    
    Args:
        product_id: معرف المنتج (ID) الذي يريد العميل شراءه.
        customer_name: اسم العميل
        customer_phone: رقم هاتف العميل
        city: مدينة العميل
        address: العنوان التفصيلي للعميل
        payment_method: طريقة الدفع
    """
    import re
    # التحقق من رقم الهاتف (أرقام فقط)
    clean_phone = "".join(filter(str.isdigit, customer_phone))
    
    # فحص الرقم الفلسطيني
    if not (clean_phone.startswith("059") or clean_phone.startswith("056")) or len(clean_phone) != 10:
        return "رقم الهاتف غير صالح. يرجى طلب رقم جوال فلسطيني صحيح يبدأ بـ 059 أو 056 ومكون من 10 أرقام لحفظ الطلب."
        
    # محاولة حفظ الطلب في قاعدة بيانات SQLite
    order_id = save_order(product_id, customer_name, clean_phone, city, address, payment_method, db_path=SQLITE_DB_PATH)
    if order_id:
        return f"تم حفظ الطلب بنجاح. رقم الطلب للعميل هو #{order_id}."
    else:
        return "حدث خطأ أثناء محاولة حفظ الطلب في قاعدة البيانات."

# نقوم بتجميع الأدوات في قائمة (List) لتمريرها لاحقاً لدالة bind_tools()
tools = [search_store_products, save_customer_order]
