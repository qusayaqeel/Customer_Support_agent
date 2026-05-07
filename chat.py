from core.agent import run_agent_loop
from core.rag import init_vector_store
from db.database import init_db
from dotenv import load_dotenv

# تحميل المتغيرات من ملف .env
load_dotenv()

print("جاري تهيئة قاعدة بيانات المنتجات...")
init_vector_store("data/products.json", "chroma_db")

print("جاري تهيئة قاعدة بيانات الطلبات...")
init_db("orders.db")

print("\n" + "="*50)
print("مرحباً بك في المساعد الذكي! (اكتب 'خروج' لإنهاء المحادثة)")
print("="*50 + "\n")

# سنحتفظ بجلسة المحادثة ليتذكر الـ Agent سياق الكلام
chat_session = None

while True:
    user_input = input("أنت: ")
    if user_input.strip() == "":
        continue
    if user_input.strip() == "خروج":
        print("وداعاً!")
        break
        
    try:
        # استدعاء العقل المدبر وإرسال الرسالة
        response_text, chat_session = run_agent_loop(user_input, chat_session=chat_session)
        print(f"\nالـ Agent: {response_text}\n")
    except Exception as e:
        print(f"\nحدث خطأ: {e}\n")
