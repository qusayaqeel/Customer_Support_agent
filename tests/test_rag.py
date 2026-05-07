import os
import json
import pytest
from core.rag import init_vector_store, search_products

def test_init_vector_store(tmp_path):
    """
    هذا الفحص يتأكد من أن دالة init_vector_store قادرة على:
    1. قراءة ملف JSON
    2. تهيئة ChromaDB
    3. حفظ المنتجات بنجاح داخل الـ Vector DB
    """
    # 1. تجهيز بيانات وهمية مخصصة للفحص فقط
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
    
    # 2. إنشاء ملف json وهمي في مسار مؤقت (tmp_path هو ميزة من pytest)
    fake_file_path = tmp_path / "fake_products.json"
    fake_file_path.write_text(json.dumps(fake_products, ensure_ascii=False), encoding='utf-8')
    
    # تحديد مسار مؤقت لقاعدة بيانات Chroma
    fake_db_path = str(tmp_path / "chroma_db")
    
    # 3. استدعاء الدالة اللي لسه ما برمجناها (لكن بدنا نفحصها)
    # لاحظ إننا بنمررها المسارات الوهمية عشان ما نخرب البيانات الحقيقية
    collection = init_vector_store(file_path=str(fake_file_path), db_path=fake_db_path)
    
    # 4. التأكد من النتائج (Assertions)
    assert collection is not None, "الدالة لازم ترجع كائن Collection من ChromaDB"
    assert collection.count() == 1, "قاعدة البيانات لازم يكون فيها منتج واحد فقط زي ما أعطيناها"
    
    # التأكد من أن المنتج انحفظ بالـ ID الصحيح
    results = collection.get(ids=["test_1"])
    assert results["ids"][0] == "test_1", "المنتج لم يتم حفظه بالـ ID الصحيح"


def test_search_products(tmp_path):
    """
    فحص دالة البحث للتأكد من قدرتها على جلب المنتجات حسب المعنى.
    """
    # 1. التجهيز (Setup) بنفس الطريقة
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
    
    # إنشاء الـ Collection باستخدام الدالة الأولى اللي برمجناها
    collection = init_vector_store(file_path=str(fake_file_path), db_path=fake_db_path)
    
    # 2. استدعاء الدالة (Function Call) اللي بدنا نبرمجها هسا
    # رح نبحث عن كلمة "حاسوب"، مع إنو المنتج اسمه "لابتوب"، عشان نفحص البحث بالمعنى الدلالي
    search_results = search_products(query="حاسوب", collection=collection, n_results=1)
    
    # 3. التحقق (Assertions)
    assert len(search_results) > 0, "لازم يرجع نتيجة بحث واحدة على الأقل"
    assert search_results[0]["id"] == "test_1", "المنتج اللي رجع مش هو المنتج الصحيح!"
