import sqlite3
import os
import pytest
from db.database import init_db, save_order

def test_init_db(tmp_path):
    """
    هذا الفحص يتأكد من أن دالة init_db قادرة على إنشاء ملف قاعدة البيانات وجدول الطلبات.
    """
    # 1. التجهيز: تحديد مسار مؤقت (وهمي) لقاعدة البيانات
    db_path = str(tmp_path / "test_orders.db")
    
    # 2. الاستدعاء: نطلب من الدالة تبني قاعدة البيانات في هذا المسار
    init_db(db_path=db_path)
    
    # 3. التحقق (Assertions):
    # نتأكد أولاً إنو الملف الفعلي تم إنشاؤه
    assert os.path.exists(db_path), "ملف قاعدة البيانات لم يتم إنشاؤه"
    
    # نتأكد إنو جدول (orders) موجود جوا القاعدة
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    # استعلام للبحث عن اسم الجدول في السجلات الأساسية لـ SQLite
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='orders';")
    table_exists = cursor.fetchone()
    conn.close()
    
    assert table_exists is not None, "جدول الطلبات (orders) غير موجود!"


def test_save_order(tmp_path):
    """
    هذا الفحص يتأكد من أن دالة save_order قادرة على حفظ بيانات الطلب بنجاح.
    """
    # 1. التجهيز: إنشاء قاعدة بيانات وهمية
    db_path = str(tmp_path / "test_orders.db")
    init_db(db_path=db_path)
    
    # 2. الاستدعاء: استدعاء دالة الحفظ مع بيانات وهمية
    result = save_order(
        product_id="test_p1", 
        customer_name="أحمد", 
        customer_phone="0599000000",
        db_path=db_path
    )
    
    # 3. التحقق: لازم الدالة ترجع True كدليل على النجاح
    assert result is True, "الدالة لازم ترجع True عند نجاح الحفظ"
    
    # نتأكد إنو البيانات فعلاً نزلت في الجدول
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT product_id, customer_name, customer_phone FROM orders")
    row = cursor.fetchone()
    conn.close()
    
    assert row is not None, "ما في أي طلب انحفظ في القاعدة!"
    assert row[0] == "test_p1"
    assert row[1] == "أحمد"
    assert row[2] == "0599000000"
