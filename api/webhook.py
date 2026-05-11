import os
import requests
import time
from fastapi import APIRouter, Request, BackgroundTasks
from langchain_core.messages import HumanMessage
from agent.graph import agent_graph

router = APIRouter()

# ذاكرة مؤقتة لحفظ جلسات المحادثة
user_sessions = {}
SESSION_TIMEOUT = 30 * 60  # 30 دقيقة
MAX_MESSAGES = 20  # الاحتفاظ بآخر 20 رسالة فقط (10 ذهاب و 10 إياب)

def send_telegram_message(chat_id: int, text: str):
    """إرسال رسالة إلى تيليجرام"""
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text
    }
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
    except Exception as e:
        print(f"Error sending message to Telegram: {e}")

def process_telegram_update(chat_id: int, user_text: str):
    """معالجة رسائل تيليجرام وإدارة الذاكرة (Session Management)"""
    current_time = time.time()
    
    # 1. تصفير الجلسة إذا أرسل العميل /start
    if user_text.strip() == "/start":
        if chat_id in user_sessions:
            del user_sessions[chat_id]
        send_telegram_message(chat_id, "يا هلا فيك بمتجر سمارت ستور! أنا أبو العبد، تفضل كيف بقدر أساعدك اليوم؟")
        return

    # 2. جلب الجلسة الحالية
    session = user_sessions.get(chat_id)
    
    # 3. فحص وقت انتهاء الجلسة (TTL)
    if session:
        last_activity = session.get("last_activity", 0)
        if current_time - last_activity > SESSION_TIMEOUT:
            print(f"Session expired for {chat_id}. Creating new session.")
            session = None  # تصفير
            
    if not session:
        session = {
            "messages": [],
            "funnel_stage": "greeting",
            "guardrail_passed": True,
            "last_activity": current_time
        }
        
    try:
        # 4. تقليم الرسائل القديمة (Sliding Window)
        messages_history = session["messages"]
        if len(messages_history) > MAX_MESSAGES:
            # نحتفظ بآخر MAX_MESSAGES رسالة (مع الحرص على عدم كسر الـ Tool calls)
            messages_history = messages_history[-MAX_MESSAGES:]
            
        # 5. تجهيز المدخلات
        new_input = {
            "messages": messages_history + [HumanMessage(content=user_text)],
            "funnel_stage": session.get("funnel_stage", "greeting"),
            "guardrail_passed": True
        }
        
        # 6. إطلاق الـ Graph
        new_state = agent_graph.invoke(new_input)
        
        # 7. تحديث الذاكرة
        new_state["last_activity"] = current_time
        user_sessions[chat_id] = new_state
        
        # 8. استخراج وإرسال الرد
        response_text = new_state["messages"][-1].content
        send_telegram_message(chat_id, response_text)
        
    except Exception as e:
        print(f"Agent Graph Error: {e}")
        send_telegram_message(chat_id, "عذراً، أواجه مشكلة تقنية حالياً. يرجى المحاولة لاحقاً.")

@router.post("/webhook")
async def telegram_webhook(request: Request, background_tasks: BackgroundTasks):
    """
    هذه هي نقطة الاستقبال (Endpoint) التي سيقوم تيليجرام بإرسال الرسائل الجديدة إليها.
    """
    # قراءة البيانات المرسلة من تيليجرام
    data = await request.json()
    
    # التأكد من أن التحديث يحتوي على رسالة نصية
    if "message" in data and "text" in data["message"]:
        chat_id = data["message"]["chat"]["id"]
        user_text = data["message"]["text"]
        
        # إضافة المهمة لتعمل في الخلفية لكي نرد على تيليجرام فوراً بـ 200 OK
        # لأن تيليجرام إذا لم يستلم 200 OK بسرعة، سيقوم بإعادة إرسال الرسالة عدة مرات!
        background_tasks.add_task(process_telegram_update, chat_id, user_text)
        
    return {"status": "ok"}
