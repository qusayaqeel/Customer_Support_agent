import os
import json
from groq import Groq
from core.rag import init_vector_store, search_products
from db.database import save_order

def run_agent_loop(user_message: str, chat_session=None, db_path="chroma_db", sqlite_db_path="orders.db", products_file="data/products.json"):
    """
    العقل المدبر المحدث (Groq Version).
    """
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY is not set in environment variables.")
        
    client = Groq(api_key=api_key)
    
    # 1. تعريف الأدوات (Tools) بصيغة JSON Schema القياسية
    tools = [
        {
            "type": "function",
            "function": {
                "name": "search_store_products",
                "description": "استخدم هذه الأداة للبحث عن المنتجات في المتجر بناءً على طلب المستخدم. (مثل: لابتوب، ايفون، ساعات)",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "كلمة البحث (مثال: لابتوب ديل، ايفون 15)"
                        }
                    },
                    "required": ["query"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "save_customer_order",
                "description": "استخدم هذه الأداة لحفظ طلب العميل عندما يؤكد رغبته في شراء منتج محدد. يجب أن تطلب اسمه ورقم هاتفه أولاً.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "product_id": {
                            "type": "string",
                            "description": "معرف المنتج (ID) الذي يريد العميل شراءه."
                        },
                        "customer_name": {
                            "type": "string",
                            "description": "اسم العميل"
                        },
                        "customer_phone": {
                            "type": "string",
                            "description": "رقم هاتف العميل"
                        }
                    },
                    "required": ["product_id", "customer_name", "customer_phone"]
                }
            }
        }
    ]

    # 2. إعداد الذاكرة (Chat Session)
    # في المعيار العالمي الذاكرة هي عبارة عن List من الـ Dictionaries
    if chat_session is None:
        chat_session = []
        # إضافة التعليمات الأساسية (System Prompt) في بداية المحادثة
        chat_session.append({
            "role": "system",
            "content": "أنت مساعد ذكي لمتجر إلكترونيات عربي. استخدم أداة البحث للبحث عن منتجات، وأداة الحفظ لتسجيل الطلبات. تحدث باللغة العربية بأسلوب ودود ومختصر. لا تقل أبداً أنك نموذج لغوي."
        })
        
    # إضافة رسالة المستخدم الجديدة للذاكرة
    chat_session.append({"role": "user", "content": user_message})
    
    # 3. الـ Manual Loop لاستدعاء الدوال
    while True:
        # إرسال المحادثة للموديل
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant", # الموديل الجديد المعتمد بدلاً من القديم
            messages=chat_session,
            tools=tools,
            tool_choice="auto"
        )
        
        response_message = response.choices[0].message
        
        # هل الموديل يطلب استخدام دالة؟
        tool_calls = response_message.tool_calls
        if tool_calls:
            # إضافة رسالة الموديل (التي تحتوي على طلب الدالة) للذاكرة
            chat_session.append(response_message)
            
            # تنفيذ كل الدوال التي طلبها الموديل
            for tool_call in tool_calls:
                function_name = tool_call.function.name
                function_args = json.loads(tool_call.function.arguments)
                
                # تنفيذ دالة البحث
                if function_name == "search_store_products":
                    query = function_args.get("query")
                    collection = init_vector_store(file_path=products_file, db_path=db_path)
                    results = str(search_products(query, collection))
                    
                    # حفظ النتيجة في الذاكرة
                    chat_session.append({
                        "tool_call_id": tool_call.id,
                        "role": "tool",
                        "name": function_name,
                        "content": results,
                    })
                    
                # تنفيذ دالة الحفظ
                elif function_name == "save_customer_order":
                    product_id = function_args.get("product_id")
                    customer_name = function_args.get("customer_name")
                    customer_phone = function_args.get("customer_phone")
                    
                    success = save_order(product_id, customer_name, customer_phone, db_path=sqlite_db_path)
                    result_msg = "تم الحفظ بنجاح" if success else "فشل الحفظ"
                    
                    chat_session.append({
                        "tool_call_id": tool_call.id,
                        "role": "tool",
                        "name": function_name,
                        "content": result_msg,
                    })
            
            # بعد إرفاق نتائج الدوال، نعيد الدوران (Loop) لنسأل الموديل مجدداً
            continue
            
        else:
            # إذا لم يطلب الموديل أي دالة، فهذا يعني أنه أعطانا الرد النهائي النصي
            final_text = response_message.content
            # نحفظ الرد النهائي في الذاكرة
            chat_session.append({"role": "assistant", "content": final_text})
            
            return final_text, chat_session
