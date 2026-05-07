import os
import pytest
from dotenv import load_dotenv

# Ensure we load the environment variables (like GEMINI_API_KEY)
load_dotenv()

# We import the function that we are going to build
from core.agent import run_agent_loop

# Skip tests if there is no API key
pytestmark = pytest.mark.skipif(
    not os.getenv("GEMINI_API_KEY"), 
    reason="GEMINI_API_KEY not found in .env file"
)

def test_agent_general_conversation():
    """
    فحص المحادثة العادية:
    يجب أن يكون الوكيل قادراً على الرد على التحية بدون استخدام أدوات.
    """
    response, _ = run_agent_loop("مرحبا، أنا اسمي أحمد.")
    
    # التأكد من أن الرد نصي وليس فارغاً
    assert response is not None
    assert isinstance(response, str)
    assert len(response) > 5

def test_agent_search_products():
    """
    فحص طلب البحث:
    عندما نسأل عن منتج، يجب أن يستخدم أداة البحث ويرجع إجابة تحتوي على معلومات المنتج.
    ملاحظة: هذا يتطلب وجود بعض المنتجات في قاعدة البيانات.
    """
    # تهيئة قاعدة البيانات الوهمية للاختبار (Vector DB)
    from core.rag import init_vector_store
    import json
    
    fake_products = [{"id": "laptop_1", "name": "لابتوب سحري", "description": "لابتوب خرافي للمبرمجين", "price_ils": 5000, "category": "laptops", "stock": 10}]
    with open("fake_products.json", "w", encoding="utf-8") as f:
        json.dump(fake_products, f, ensure_ascii=False)
        
    init_vector_store("fake_products.json", "fake_chroma_db")
    
    # سؤال الآلة عن اللابتوب
    response, _ = run_agent_loop("هل يوجد لديكم لابتوب للمبرمجين؟", db_path="fake_chroma_db", products_file="fake_products.json")
    
    assert response is not None
    assert "سحري" in response or "لابتوب" in response
    
    # تنظيف الملفات
    os.remove("fake_products.json")

def test_agent_save_order():
    """
    فحص طلب الشراء:
    عندما يطلب العميل الشراء مع إعطاء بياناته، يجب أن يستخدم أداة حفظ الطلب.
    """
    # رسالة واضحة تحتوي على معلومات الشراء
    from db.database import init_db
    init_db("test_orders.db")
    msg = "أريد شراء المنتج laptop_1، اسمي محمد ورقمي 0599999999"
    response, _ = run_agent_loop(msg, sqlite_db_path="test_orders.db")
    
    assert response is not None
    # يفترض أن الرد يؤكد عملية الشراء
    
    # نتحقق من قاعدة البيانات
    import sqlite3
    conn = sqlite3.connect("test_orders.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM orders WHERE customer_name='محمد'")
    order = cursor.fetchone()
    conn.close()
    
    assert order is not None, "لم يتم حفظ الطلب في قاعدة البيانات!"
    assert order[1] == "laptop_1"
    
    # تنظيف ملف الداتا بيس
    os.remove("test_orders.db")
