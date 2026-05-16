import sqlite3
from datetime import datetime

def init_db(db_path: str = "orders.db"):
    """
    Creates the SQLite database and orders table if they don't exist.
    Also handles schema migration for older databases.
    """
    # 1. Open connection (file is auto-created if it doesn't exist)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 2. Create orders table (IF NOT EXISTS prevents errors on re-runs)
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
    
    # Migrate: add new columns to older table schemas if they exist
    try:
        cursor.execute('ALTER TABLE orders ADD COLUMN city TEXT')
        cursor.execute('ALTER TABLE orders ADD COLUMN address TEXT')
        cursor.execute('ALTER TABLE orders ADD COLUMN payment_method TEXT')
    except sqlite3.OperationalError:
        pass
    
    # 3. Commit changes and close connection
    conn.commit()
    conn.close()


def save_order(product_id: str, customer_name: str, customer_phone: str, city: str = "", address: str = "", payment_method: str = "", db_path: str = "orders.db"):
    """
    Saves a new order to the database and returns the order ID.
    Uses parameterized queries to prevent SQL injection.
    """
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Parameterized query (? placeholders) to prevent SQL injection
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
