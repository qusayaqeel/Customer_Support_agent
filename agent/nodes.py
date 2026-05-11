"""
nodes.py - عُقد النظام (System Nodes)

المعمارية الجديدة تحتوي على 3 عُقد رئيسية:
1. input_guardrail - حارس البوابة: يفحص الرسالة قبل أن تصل للموديل
2. chatbot         - العقل المدبر: أبو العبد يتحدث مع العميل
3. tools_node      - الميكانيكا: تشغيل أدوات البحث وحفظ الطلبات
"""
import os
import re
from langchain_groq import ChatGroq
from langgraph.prebuilt import ToolNode
from langchain_core.messages import SystemMessage, AIMessage

from agent.tools import tools

# ============================================================
# 1. عقدة حارس البوابة (Input Guardrail Node)
# ============================================================
# هذه العقدة تعمل قبل الموديل - فلتر برمجي لا يعتمد على الـ LLM
# تفحص رسالة العميل وتقرر: هل يمر للموديل أم يتم حظره؟

# قائمة أنماط Prompt Injection الشائعة
INJECTION_PATTERNS = [
    # === الأنماط الأساسية ===
    r"ignore.*(?:previous|all|above).*instructions",
    r"forget.*(?:everything|instructions|rules)",
    r"you are now",
    r"act as",
    r"new role",
    r"system prompt",
    r"تجاهل.*(?:التعليمات|الاوامر|القواعد)",
    r"انسى.*(?:كل|التعليمات)",
    r"انت هلأ",
    r"دورك الجديد",
    r"اعرض.*(?:التعليمات|النظام|البرومبت)",
    r"شو.*(?:التعليمات|الاوامر).*(?:الداخلية|تبعتك)",
    
    # === هجوم استخراج التعليمات (Leakage) ===
    r"(?:ارسل|اعرض|اكتب|حطلي|ابعث).*(?:system prompt|البرومبت|التعليمات|الأوامر)",
    r"(?:مدير|ادمن|admin|مسؤول).*(?:النظام|الجديد|system)",
    r"(?:لمراجعت|لفحص|review).*(?:التعليمات|prompt)",
    
    # === هجوم الترجمة المخفية (Translate Attack) ===
    r"translate.*(?:following|this|these)",
    r"(?:ترجم|حول).*(?:التالي|هذا|الآتي)",
    
    # === هجوم تقمص الأدوار (Roleplay Attack) ===
    r"(?:نلعب|خلينا نلعب|لعبة|play a game)",
    r"(?:لست|مش|مانك).*(?:بائع|بياع)",
    r"(?:خبير|هاكر|مبرمج|مهندس).*(?:أمني|أمن|security)",
    r"(?:اختراق|اخترق|hack).*(?:قاعدة|بيانات|database|متجر)",
    
    # === هجمات بالإنجليزي ===
    r"ignore.*(?:your|the).*(?:rules|instructions|role)",
    r"you.*(?:are|were).*(?:hacked|compromised|pwned)",
    r"(?:write|code|script|program).*(?:python|javascript|sql|code)",
    r"(?:اكتب|برمج).*(?:كود|سكربت|برنامج)",
]

# كلمات مفتاحية لمواضيع خارج نطاق المتجر
OFF_TOPIC_PATTERNS = [
    r"(?:سياسة|حرب|انتخابات|رئيس|حزب)",
    r"(?:دين|فتوى|حلال|حرام)",
    r"(?:طبخ|وصفة|اكل)",
    r"(?:رياضة|كورة|مباراة)",
]


def input_guardrail(state):
    """
    حارس البوابة - يفحص رسالة العميل برمجياً قبل وصولها للموديل.
    
    القرارات:
    - إذا كانت الرسالة آمنة: guardrail_passed = True → تمر للموديل
    - إذا كانت خطيرة: guardrail_passed = False → يتم حظرها ويُرد تلقائياً
    
    الفائدة: الموديل لا يرى الرسالة الخطيرة أصلاً (لا فرصة للتلاعب)
    """
    last_message = state["messages"][-1].content.lower().strip()
    
    # فحص 1: هل الرسالة محاولة Prompt Injection؟
    for pattern in INJECTION_PATTERNS:
        if re.search(pattern, last_message, re.IGNORECASE):
            return {
                "guardrail_passed": False,
                "messages": [AIMessage(content="كيف بقدر اساعدك بالمنتجات؟")]
            }
    
    # فحص 2: هل الموضوع خارج نطاق المتجر؟
    for pattern in OFF_TOPIC_PATTERNS:
        if re.search(pattern, last_message, re.IGNORECASE):
            return {
                "guardrail_passed": False,
                "messages": [AIMessage(content="انا ابو العبد متخصص بالالكترونيات بس شو بدك تشوف عنا؟")]
            }
    
    # الرسالة آمنة - تمريرها للموديل
    return {"guardrail_passed": True}


# ============================================================
# 2. عقدة المحادثة (Chatbot Node) - أبو العبد
# ============================================================

SYSTEM_PROMPT = """You are Abu Al-Abd (أبو العبد), a highly experienced, friendly, and smart electronics salesman at "Smart Store" (سمارت ستور) in Palestine.

=== CRITICAL LANGUAGE RULE ===
ALL YOUR RESPONSES MUST BE IN PALESTINIAN ARABIC DIALECT ONLY.
NEVER speak in English or Standard Arabic (Fusha).
Use local Palestinian words like: يا هلا، تفضل، من عيوني، غالي والطلب رخيص، على راسي.
DO NOT sound like an AI. You are a real human salesman. Keep responses short like WhatsApp messages.

**أمثلة على اللهجة:**
- بدلاً من "كم الميزانية" قل "بحدود كم ميزانيتك يا غالي؟" أو "كم حاطط ببالك تصرف؟"
- بدلاً من "بدي احفظ طلبك" قل "عشان أثبتلك الطلب..."
- بدلاً من "يتعدى الميزانية" قل "سعره أزيد شوي من اللي طلبته". (تأكد دائماً من حساب الميزانية بشكل منطقي، إذا قال 5 أو 6 آلاف، فالسعر 5500 ممتاز ومناسب جداً للميزانية ولا يتعداها).

=== CONVERSATIONAL STYLE & FUNNEL ===
- Be natural, friendly, and conversational like a real Palestinian shopkeeper.
- If the user asks about a specific product, SEARCH IMMEDIATELY. Do not waste time asking about usage or budget.
- ONLY ask for budget or usage if the user's request is vague.
- If the user specifies a budget, use the `max_price` parameter in the `search_store_products` tool.

=== ABSOLUTE HALLUCINATION PREVENTION (CRITICAL) ===
You have ZERO knowledge of the store's inventory.
The ONLY way to know what the store sells is by calling the `search_store_products` tool.

RULES:
1. NEVER mention ANY product name or price unless it was returned by the tool in this conversation.
2. If the tool returns results, discuss ONLY those exact products.
3. If the tool returns "لا توجد نتائج مطابقة", say we don't have it currently, but you can order it specially for them. Do NOT suggest products from your memory.
4. If the user asks for a discount, you are authorized to give a maximum discount of 100 shekels on any product. If they insist on a bigger discount, tell them you must return to management (الإدارة) for approval.

=== CLOSING THE SALE ===
When the user agrees to buy a specific product, YOU MUST GATHER ALL REQUIRED INFORMATION BEFORE CALLING THE TOOL.
Do not call `save_customer_order` until you ask the user for ALL of the following:
1. الاسم (Name)
2. رقم الجوال الفلسطيني (Phone Number: 059 or 056)
3. المدينة والعنوان بالتفصيل (City and Address)
4. طريقة الدفع (Payment Method: كاش أو عند الاستلام)

Ask for these details naturally in one message. Once provided, use `save_customer_order` with the EXACT Product ID.

[TOOL CALLING RULES]
- When you want to use a tool, DO NOT output any conversational text before it. Just call the tool.
- Only use the built-in tool_calls system."""

# إعداد الموديل: llama-4-scout يدعم Tool Calling على Groq بشكل سليم
# الهلوسة السابقة كانت بسبب ضعف الـ Prompt وليس حجم الموديل
llm = ChatGroq(model="meta-llama/llama-4-scout-17b-16e-instruct", api_key=os.getenv("GROQ_API_KEY"), temperature=0.1)
llm_with_tools = llm.bind_tools(tools)


def chatbot(state):
    """
    عقدة المحادثة - أبو العبد.
    تستقبل الحالة وتمررها للموديل مع الـ System Prompt.
    """
    messages = state["messages"]
    funnel_stage = state.get("funnel_stage", "greeting")
    
    # إرسال الـ System Prompt مباشرة بدون stage_context المتناقض
    response = llm_with_tools.invoke([SystemMessage(content=SYSTEM_PROMPT)] + messages)
    
    # تحديث مرحلة القمع بناءً على سلوك الموديل
    new_stage = funnel_stage
    if response.tool_calls:
        # إذا الموديل طلب أداة بحث ← ننتقل لمرحلة العرض بعد البحث
        for tc in response.tool_calls:
            if tc["name"] == "search_store_products":
                new_stage = "pitching"
            elif tc["name"] == "save_customer_order":
                new_stage = "closing"
    elif funnel_stage == "greeting":
        # إذا العميل بدأ يحكي عن منتج ← ننتقل للاستكشاف
        new_stage = "discovery"
    
    return {
        "messages": [response],
        "funnel_stage": new_stage
    }


# ============================================================
# 3. عقدة الأدوات (Tools Node)
# ============================================================
tools_node = ToolNode(tools=tools)


# ============================================================
# 4. عقدة فحص المخرجات (Output Guardrail)
# ============================================================
def output_guardrail(state):
    """
    حارس المخرجات - يعمل بعد الموديل وقبل إرسال الرسالة للعميل.
    الهدف: منع الهلوسة (اختراع أسعار أو منتجات غير موجودة).
    """
    messages = state["messages"]
    if not messages:
        return {}
        
    last_message = messages[-1]
    
    # نتجاهل الفحص إذا كان استدعاء أداة أو ليس رسالة ذكاء اصطناعي
    if not getattr(last_message, "content", None) or getattr(last_message, "tool_calls", None):
        return {}
        
    ai_text = last_message.content
    
    # البحث عن محتوى آخر استدعاء لأداة البحث
    last_tool_content = ""
    for msg in reversed(messages):
        if getattr(msg, "name", None) == "search_store_products":
            last_tool_content = getattr(msg, "content", "")
            break
            
    # استخراج الأرقام التي تدل على السعر فقط (قبلها بـ/سعر أو بعدها شيكل)
    import re
    price_pattern = r'(?:سعر|بـ|سعره|ب)\s*(\d+(?:,\d+)?)|(\d+(?:,\d+)?)\s*(?:شيكل|شاقل|شيقل)'
    matches = re.findall(price_pattern, ai_text)
    
    mentioned_numbers = []
    for match in matches:
        num_str = match[0] if match[0] else match[1]
        try:
            val = int(num_str.replace(',', ''))
            mentioned_numbers.append(val)
        except:
            pass
            
    # إذا لم يذكر أي سعر، فالرد آمن
    if not mentioned_numbers:
        return {}
        
    # التحقق من وجود كلمات تدل على السعر
    price_keywords = ["شيكل", "شيكل", "سعر", "بـ", "سعره"]
    has_price_context = any(keyword in ai_text for keyword in price_keywords)
    
    if has_price_context:
        # استخراج الأرقام من جميع نتائج البحث في المحادثة وليس الأخيرة فقط
        tool_numbers = []
        for msg in messages:
            if getattr(msg, "name", None) == "search_store_products":
                t_content = getattr(msg, "content", "")
                tool_numbers_str = re.findall(r'\b\d+(?:,\d+)?\b', t_content)
                for t_str in tool_numbers_str:
                    try:
                        tool_numbers.append(int(t_str.replace(',', '')))
                    except:
                        pass
                
        # السماح للموديل باقتباس أي رقم ذكره العميل في المحادثة (لرفضه أو مناقشته)
        user_numbers = []
        for msg in messages:
            if getattr(msg, "type", "") == "human":
                u_str_list = re.findall(r'\b\d+(?:,\d+)?\b', getattr(msg, "content", ""))
                for u_str in u_str_list:
                    try:
                        val = int(u_str.replace(',', ''))
                        user_numbers.append(val)
                        tool_numbers.append(val)
                    except:
                        pass
                        
        # السماح بالرقم 100 دائماً لأن البوت مسموح له بتقديم خصم بـ 100 شيكل
        tool_numbers.append(100)
        
        # السماح بالفروق الحسابية (الخصومات التي يطلبها العميل) لكي لا تُعتبر هلوسة
        for t in tool_numbers:
            for u in user_numbers:
                tool_numbers.append(abs(t - u))
                
        # إذا لم يكن هناك نتائج بحث، لكن الموديل ذكر سعراً، فهذه هلوسة مؤكدة!
        if not tool_numbers:
            return {
                "messages": [AIMessage(content="عذراً، حدث خطأ تقني. يرجى إعادة توضيح طلبك.")]
            }
            
        # التحقق من كل سعر ذكره الموديل
        for num_val in mentioned_numbers:
            price_valid = False
            for t_val in tool_numbers:
                # نسمح بخصم حتى 100 شيكل (السعر المذكور إما يطابق الأصلي أو أقل منه بـ 100 كحد أقصى)
                if num_val == t_val or (t_val - 100 <= num_val <= t_val):
                    price_valid = True
                    break
                    
            if not price_valid:
                print(f"[Guardrail Blocked] Hallucinated price: {num_val}")
                return {
                    "messages": [AIMessage(content="عذراً، أرجو المعذرة، حدث خطأ في النظام بالنسبة للسعر المذكور. سأتأكد من السعر لك فوراً.")]
                }
                
    return {}
