from typing import Optional, Union
from langchain_core.tools import tool
from core.rag import init_vector_store, search_products
from db.database import save_order

# Fixed database paths for tool access
CHROMA_DB_PATH = "chroma_db"
PRODUCTS_FILE = "data/products.json"
SQLITE_DB_PATH = "orders.db"

@tool
def search_store_products(query: str, max_price: Union[int, str, None] = None) -> str:
    """
    Search for products in the store based on the user's query.
    
    Args:
        query: Search keywords (should be in Arabic for best results).
        max_price: Optional maximum price filter if the user mentions a budget.
    """
    import json
    from core.rag import init_vector_store, search_products
    
    if isinstance(max_price, str):
        try:
            max_price = int(max_price)
        except ValueError:
            max_price = None
            
    # Clean the query
    cleaned_query = query.strip()
    if not cleaned_query or len(cleaned_query) < 2:
        return "لا توجد نتائج مطابقة للبحث يرجى تحديد المنتج المطلوب بشكل اوضح"
    
    # Sanitize dangerous characters (extra protection)
    cleaned_query = cleaned_query.replace(";", "").replace("--", "").replace("DROP", "").replace("DELETE", "").replace("UPDATE", "")
    
    collection = init_vector_store(file_path=PRODUCTS_FILE, db_path=CHROMA_DB_PATH)
    results = search_products(cleaned_query, collection, max_price=max_price)
    
    if not results:
        return "لا توجد نتائج مطابقة لبحثك."
        
    import json
    # Return results as JSON string for structured backend processing
    return json.dumps(results, ensure_ascii=False)

@tool
def save_customer_order(product_id: str, customer_name: str, customer_phone: str, city: str = "", address: str = "", payment_method: str = "") -> str:
    """
    Save a customer order when they confirm purchase of a specific product.
    All required fields must be collected before calling this tool.
    
    Args:
        product_id: The product ID the customer wants to buy.
        customer_name: Customer's full name.
        customer_phone: Customer's Palestinian phone number (10 digits, starts with 059 or 056).
        city: Customer's city.
        address: Customer's detailed address.
        payment_method: Payment method (cash or cash on delivery).
    """
    import re
    
    # Validate name (must not be empty or too short)
    if not customer_name or len(customer_name.strip()) < 2:
        return "الاسم غير صالح. يرجى طلب الاسم الكامل من العميل."
    
    # Validate phone number (digits only)
    clean_phone = "".join(filter(str.isdigit, customer_phone))
    
    # Palestinian phone number validation
    if not (clean_phone.startswith("059") or clean_phone.startswith("056")) or len(clean_phone) != 10:
        return "رقم الهاتف غير صالح. يرجى طلب رقم جوال فلسطيني صحيح يبدأ بـ 059 أو 056 ومكون من 10 أرقام. مثال: 0591234567 أو 0561234567."
    
    # Validate city (must not be empty)
    if not city or len(city.strip()) < 2:
        return "المدينة غير محددة. يرجى سؤال العميل عن المدينة والعنوان بالتفصيل."
        
    # Save order to SQLite database
    order_id = save_order(product_id, customer_name.strip(), clean_phone, city.strip(), address.strip(), payment_method.strip(), db_path=SQLITE_DB_PATH)
    if order_id:
        return f"تم حفظ الطلب بنجاح. رقم الطلب للعميل هو #{order_id}."
    else:
        return "حدث خطأ أثناء محاولة حفظ الطلب في قاعدة البيانات."

# Collect tools into a list for bind_tools()
tools = [search_store_products, save_customer_order]
