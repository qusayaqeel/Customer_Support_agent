import os
import json
import pytest
from core.rag import init_vector_store, search_products

def test_init_vector_store(tmp_path):
    """
    Verify that init_vector_store can:
    1. Read a JSON file
    2. Initialize ChromaDB
    3. Successfully store products in the Vector DB
    """
    # 1. Setup: fake test data
    fake_products = [
        {
            "id": "test_1",
            "name": "لابتوب فحص",
            "description": "لابتوب مخصص لاختبار الكود",
            "price_ils": 2000,
            "category": "لابتوبات",
            "stock": 5
        }
    ]
    
    # 2. Create a temporary fake JSON file (tmp_path is a pytest fixture)
    fake_file_path = tmp_path / "fake_products.json"
    fake_file_path.write_text(json.dumps(fake_products, ensure_ascii=False), encoding='utf-8')
    
    fake_db_path = str(tmp_path / "chroma_db")
    
    # 3. Call the function with fake paths (to not corrupt real data)
    collection = init_vector_store(file_path=str(fake_file_path), db_path=fake_db_path)
    
    # 4. Assertions
    assert collection is not None, "Function must return a ChromaDB Collection object"
    assert collection.count() == 1, "Database must contain exactly 1 product"
    
    # Verify the product was saved with the correct ID
    results = collection.get(ids=["test_1"])
    assert results["ids"][0] == "test_1", "Product was not saved with the correct ID"


def test_search_products(tmp_path):
    """
    Verify semantic search can find products by meaning (not just exact match).
    Search for 'حاسوب' (computer) should find 'لابتوب' (laptop).
    """
    # 1. Setup: same fake data
    fake_products = [
        {
            "id": "test_1",
            "name": "لابتوب فحص",
            "description": "لابتوب مخصص لاختبار الكود",
            "price_ils": 2000,
            "category": "لابتوبات",
            "stock": 5
        }
    ]
    fake_file_path = tmp_path / "fake_products.json"
    fake_file_path.write_text(json.dumps(fake_products, ensure_ascii=False), encoding='utf-8')
    fake_db_path = str(tmp_path / "chroma_db_search")
    
    collection = init_vector_store(file_path=str(fake_file_path), db_path=fake_db_path)
    
    # 2. Search for "حاسوب" (computer) - should find "لابتوب" via semantic matching
    search_results = search_products(query="حاسوب", collection=collection, n_results=1)
    
    # 3. Assertions
    assert len(search_results) > 0, "Must return at least one search result"
    assert search_results[0]["id"] == "test_1", "Returned product is not the correct one"
