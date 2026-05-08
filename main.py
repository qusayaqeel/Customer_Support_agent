from fastapi import FastAPI
from dotenv import load_dotenv

# 1. تحميل متغيرات البيئة (API Keys) قبل استيراد أي ملفات أخرى لتجنب أخطاء المفاتيح السرية
load_dotenv()

from api.webhook import router as webhook_router
from core.rag import init_vector_store
from db.database import init_db

# 2. تهيئة قواعد البيانات مرة واحدة عند تشغيل السيرفر
print("جاري تهيئة قواعد البيانات...")
init_vector_store("data/products.json", "chroma_db")
init_db("orders.db")

# 3. إنشاء تطبيق FastAPI
app = FastAPI(title="Customer Support AI Agent")

# 4. ربط مسارات الـ Webhook بالتطبيق
app.include_router(webhook_router)

@app.get("/")
def root():
    """
    نقطة فحص بسيطة للتأكد من أن السيرفر يعمل.
    """
    return {"message": "Customer Support AI Agent is running!"}
