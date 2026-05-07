import os
import requests
from fastapi import APIRouter, Request, BackgroundTasks
from core.agent import run_agent_loop

router = APIRouter()

# ذاكرة مؤقتة بسيطة لحفظ جلسات المحادثة لكل مستخدم بناءً على الـ chat_id الخاص به
user_sessions = {}

def send_telegram_message(chat_id: int, text: str):
    """
    تقوم هذه الدالة بإرسال رسالة إلى المستخدم عبر واجهة تيليجرام (Telegram Bot API).
    """
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
    """
    تقوم هذه الدالة بمعالجة الرسالة وإرسالها للعقل المدبر (الـ Agent) ثم الرد على تيليجرام.
    نضعها في دالة منفصلة لتعمل في الخلفية (Background Task) لكي لا نؤخر الرد على سيرفرات تيليجرام.
    """
    # جلب جلسة المحادثة السابقة للمستخدم (إذا كانت موجودة)
    session = user_sessions.get(chat_id)
    
    try:
        # إرسال الرسالة للعقل المدبر
        response_text, updated_session = run_agent_loop(user_text, chat_session=session)
        
        # حفظ الجلسة الجديدة ليتذكر السياق في الرسالة القادمة
        user_sessions[chat_id] = updated_session
        
        # إرسال الرد للمستخدم
        send_telegram_message(chat_id, response_text)
        
    except Exception as e:
        print(f"Agent Error: {e}")
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
