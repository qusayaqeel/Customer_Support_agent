import sqlite3
from datetime import datetime

def init_db(db_path: str = "orders.db"):
    """
    تقوم بإنشاء قاعدة بيانات SQLite وجدول الطلبات إذا لم يكن موجوداً.
    """
    # 1. فتح اتصال (وإذا الملف مش موجود رح يتم إنشاؤه تلقائياً)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 2. أمر SQL لإنشاء الجدول
    # استخدمنا IF NOT EXISTS عشان لو شغلنا الكود مرتين ما يعطي خطأ وما يمسح بياناتنا القديمة
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id TEXT NOT NULL,
            customer_name TEXT NOT NULL,
            customer_phone TEXT NOT NULL,
            city TEXT,
            address TEXT,
            payment_method TEXT,
            order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # محاولة إضافة الحقول للجدول القديم إن وجدت
    try:
        cursor.execute('ALTER TABLE orders ADD COLUMN city TEXT')
        cursor.execute('ALTER TABLE orders ADD COLUMN address TEXT')
        cursor.execute('ALTER TABLE orders ADD COLUMN payment_method TEXT')
    except sqlite3.OperationalError:
        pass
    
    # 3. حفظ التغييرات (Commit) وإغلاق الجسر (Close)
    conn.commit()
    conn.close()


def save_order(product_id: str, customer_name: str, customer_phone: str, city: str = "", address: str = "", payment_method: str = "", db_path: str = "orders.db"):
    """
    تقوم بحفظ بيانات الطلب الجديد في قاعدة البيانات.
    """
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # أمر SQL لإدخال البيانات
        # ملاحظة أمنية: بنستخدم علامات الاستفهام (?) بدل ما ندمج النصوص مباشرة 
        # عشان نمنع ثغرة أمنية خطيرة اسمها (SQL Injection)
        cursor.execute('''
            INSERT INTO orders (product_id, customer_name, customer_phone, city, address, payment_method)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (product_id, customer_name, customer_phone, city, address, payment_method))
        
        order_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return order_id
        
    except Exception as e:
        print(f"Error saving order: {e}")
        return None
