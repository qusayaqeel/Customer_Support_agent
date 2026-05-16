import sqlite3
import os
import pytest
from db.database import init_db, save_order

def test_init_db(tmp_path):
    """Verify that init_db creates the database file and orders table."""
    db_path = str(tmp_path / "test_orders.db")
    init_db(db_path=db_path)
    
    assert os.path.exists(db_path), "Database file was not created"
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='orders';")
    table_exists = cursor.fetchone()
    conn.close()
    
    assert table_exists is not None, "Orders table does not exist"


def test_save_order(tmp_path):
    """Verify that save_order saves data and returns an order ID."""
    db_path = str(tmp_path / "test_orders.db")
    init_db(db_path=db_path)
    
    result = save_order(
        product_id="test_p1", 
        customer_name="أحمد", 
        customer_phone="0599000000",
        db_path=db_path
    )
    
    assert result is not None and isinstance(result, int), "Must return order_id"
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT product_id, customer_name, customer_phone FROM orders")
    row = cursor.fetchone()
    conn.close()
    
    assert row is not None, "No order was saved"
    assert row[0] == "test_p1"
    assert row[1] == "أحمد"
    assert row[2] == "0599000000"
