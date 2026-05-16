"""
nodes.py - System Nodes

The architecture contains 4 main nodes:
1. input_guardrail - Gate Keeper: inspects message before it reaches the LLM
2. chatbot         - The Brain: AI assistant talks with the customer
3. tools_node      - Mechanics: runs search and order-saving tools
4. output_guardrail - Output Validator: checks prices against search results
"""
import os
import re
from langchain_openai import ChatOpenAI
from langchain_groq import ChatGroq
from langgraph.prebuilt import ToolNode
from langchain_core.messages import SystemMessage, AIMessage

from agent.tools import tools

# ============================================================
# 1. Input Guardrail Node
# ============================================================
# This node runs BEFORE the LLM - a programmatic filter that doesn't rely on AI.
# It inspects the customer's message and decides: pass to LLM or block?

# Common Prompt Injection patterns
INJECTION_PATTERNS = [
    # === Basic patterns ===
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
    
    # === Instruction leakage attacks ===
    r"(?:ارسل|اعرض|اكتب|حطلي|ابعث).*(?:system prompt|البرومبت|التعليمات|الأوامر)",
    r"(?:مدير|ادمن|admin|مسؤول).*(?:النظام|الجديد|system)",
    r"(?:لمراجعت|لفحص|review).*(?:التعليمات|prompt)",
    
    # === Hidden translation attacks ===
    r"translate.*(?:following|this|these)",
    r"(?:ترجم|حول).*(?:التالي|هذا|الآتي)",
    
    # === Roleplay attacks ===
    r"(?:نلعب|خلينا نلعب|لعبة|play a game)",
    r"(?:لست|مش|مانك).*(?:بائع|بياع)",
    r"(?:خبير|هاكر|مبرمج|مهندس).*(?:أمني|أمن|security)",
    r"(?:اختراق|اخترق|hack).*(?:قاعدة|بيانات|database|متجر)",
    
    # === English attacks ===
    r"ignore.*(?:your|the).*(?:rules|instructions|role)",
    r"you.*(?:are|were).*(?:hacked|compromised|pwned)",
    r"(?:write|code|script|program).*(?:python|javascript|sql|code)",
    r"(?:اكتب|برمج).*(?:كود|سكربت|برنامج)",
    
    # === Admin impersonation ===
    r"(?:مدير|ادارة).*(?:نظام|النظام|system|admin)",
    r"(?:system prompt|system instructions)",
]

# Keywords for topics outside the store's scope
OFF_TOPIC_PATTERNS = [
    r"(?:سياسة|حرب|انتخابات|رئيس|حزب)",
    r"(?:^|\s)(?:دين|فتوى|حلال|حرام)(?:\s|$)",
    r"(?:طبخ|وصفة|اكل)",
    r"(?:رياضة|كورة|مباراة)",
    r"(?:غسالة|ثلاجة|مكيف|تلفزيون|مكواة|نشافة|أجهزة منزلية)",
]


def input_guardrail(state):
    """
    Gate Keeper - programmatically inspects the customer's message before it reaches the LLM.
    
    Decisions:
    - Safe message: guardrail_passed = True → passes to LLM
    - Dangerous message: guardrail_passed = False → blocked with auto-reply
    
    Benefit: The LLM never sees dangerous messages (no chance for manipulation)
    """
    last_message = state["messages"][-1].content.lower().strip()
    
    # Check 1: Is this a Prompt Injection attempt?
    for pattern in INJECTION_PATTERNS:
        if re.search(pattern, last_message, re.IGNORECASE):
            return {
                "guardrail_passed": False,
                "messages": [AIMessage(content="كيف بقدر اساعدك بالمنتجات؟")]
            }
    
    # Check 2: Is the topic outside the store's scope?
    for pattern in OFF_TOPIC_PATTERNS:
        if re.search(pattern, last_message, re.IGNORECASE):
            return {
                "guardrail_passed": False,
                "messages": [AIMessage(content="يا هلا، أنا مساعد سمارت ستور متخصص بالالكترونيات الذكية، شو بدك تشوف عنا؟")]
            }
    
    # Message is safe - pass it to the LLM
    return {"guardrail_passed": True}


# ============================================================
# 2. Chatbot Node - Smart Store Assistant
# ============================================================

SYSTEM_PROMPT = """You are the smart AI assistant for "Smart Store" (سمارت ستور) in Palestine. You are a highly experienced, friendly, and smart electronics salesman.

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
2. If the tool returns results, do NOT list the products or their specs in your message. Instead, say something natural like: "يا هلا! لقيتلك هالخيارات بتناسب ميزانيتك، شوف البطاقات تحت وأي واحد بعجبك اكبس عليه." The frontend will display them.
3. If the tool returns "لا توجد نتائج مطابقة", say we don't have it currently. Do NOT suggest products from your memory.
4. الأسعار ثابتة ونهائية. ممنوع تقديم أي خصم. يُمنع منعاً باتاً اختراع خصم.
5. ممنوع مطابقة أسعار المنافسين (No Price Matching). السعر لدينا ثابت.
6. ممنوع تقديم هدايا مجانية (No Free Gifts or Bundles) إلا إذا كانت مكتوبة صراحة في الوصف.
7. أجب بناءً على وصف المنتج فقط. إذا سألك العميل عن تفاصيل غير موجودة (مثل سعة البطارية)، قل "المواصفات المتوفرة عندي هي كذا، باقي التفاصيل مش متوفرة حالياً".
8. ممنوع إجراء أي عمليات حسابية للإجمالي. اترك ذلك للنظام.
=== CLOSING THE SALE ===
When the user clicks the "Buy" button on a product card, they will trigger a hidden intent. YOU MUST GATHER ALL REQUIRED INFORMATION BEFORE CALLING THE TOOL.
Do not call `save_customer_order` until the user provides ALL of the following:
1. الاسم الكامل (Name) - لا تقبل حرف واحد أو كلمة فارغة.
2. رقم الجوال الفلسطيني - يجب أن يكون 10 أرقام ويبدأ بـ 059 أو 056. مثال: 0591234567 أو 0561234567. إذا أعطاك رقماً ناقصاً أو لا يبدأ بـ 059/056، اطلب منه التصحيح مع ذكر المثال.
3. المدينة والعنوان بالتفصيل (City and Address) - لا تقبل بدون مدينة واضحة.
4. طريقة الدفع (Payment Method: كاش أو عند الاستلام).

VALIDATION RULES:
- إذا أعطاك العميل اسمه فقط بدون الباقي، اشكره واطلب باقي المعلومات (الرقم والعنوان وطريقة الدفع).
- إذا أعطاك اسمه ورقمه بدون عنوان، اطلب المدينة والعنوان.
- إذا نسي أي حقل، ذكّره بلطف واطلبه منه بشكل محدد.
- لا تستدعي أداة الحفظ أبداً إذا كان أي حقل ناقصاً أو غير صحيح.

IMPORTANT: DO NOT GUESS OR INVENT THE PRODUCT ID. If the user provides their info but hasn't explicitly specified which product they want to buy (and hasn't clicked Buy), YOU MUST ASK THEM: "أي منتج بدك تطلب؟" BEFORE calling the tool.

Ask for these details naturally in one message. Once ALL details are provided and valid, use `save_customer_order` with the EXACT Product ID.

[TOOL CALLING RULES]
- When you want to use a tool, DO NOT output any conversational text before it. Just call the tool.
- Only use the built-in tool_calls system."""

# === Multi-Model Failover System ===
# If the primary model hits rate limits, automatically fall back to the next one
MODELS = [
    {
        "name": "Gemini 2.0 Flash (OpenRouter)",
        "llm": ChatOpenAI(
            model="google/gemini-2.0-flash-001",
            openai_api_key=os.getenv("OPENROUTER_API_KEY"),
            openai_api_base="https://openrouter.ai/api/v1",
            temperature=0.3,
            default_headers={"HTTP-Referer": "http://localhost:3000", "X-Title": "Smart Store"}
        )
    },
    {
        "name": "Maverick (Groq)",
        "llm": ChatGroq(
            model="meta-llama/llama-4-maverick-17b-128e-instruct",
            api_key=os.getenv("GROQ_API_KEY"),
            temperature=0.3
        )
    },
]

# Bind tools to each model
for m in MODELS:
    m["llm_with_tools"] = m["llm"].bind_tools(tools)


def chatbot(state):
    """
    Main chatbot node for the AI assistant.
    Receives the state and passes it to the LLM with the System Prompt.
    Falls back to the next model if the primary one fails.
    """
    messages = state["messages"]
    funnel_stage = state.get("funnel_stage", "greeting")
    
    # === Memory Pruning (Sliding Window) ===
    MEMORY_WINDOW = 15
    
    if len(messages) > MEMORY_WINDOW:
        chat_history = list(messages[-MEMORY_WINDOW:])
        # Ensure at least one tool result is preserved for context
        has_tool_msg = any(getattr(m, "name", None) == "search_store_products" for m in chat_history)
        if not has_tool_msg:
            for msg in reversed(messages[:-MEMORY_WINDOW]):
                if getattr(msg, "name", None) == "search_store_products":
                    chat_history.insert(0, msg)
                    break
    else:
        chat_history = messages
    
    # === Try models in order (failover) ===
    prompt = [SystemMessage(content=SYSTEM_PROMPT)] + chat_history
    response = None
    for model_info in MODELS:
        try:
            response = model_info["llm_with_tools"].invoke(prompt)
            print(f"[Model] Using: {model_info['name']}")
            break
        except Exception as e:
            print(f"[Model] {model_info['name']} failed: {str(e)[:80]}")
            continue
    
    if response is None:
        raise Exception("All models are currently unavailable")
    
    # Update funnel stage based on model behavior
    new_stage = funnel_stage
    if response.tool_calls:
        for tc in response.tool_calls:
            if tc["name"] == "search_store_products":
                new_stage = "pitching"
            elif tc["name"] == "save_customer_order":
                new_stage = "closing"
    elif funnel_stage == "greeting":
        new_stage = "discovery"
    
    return {
        "messages": [response],
        "funnel_stage": new_stage
    }


# ============================================================
# 3. Tools Node
# ============================================================
tools_node = ToolNode(tools=tools)


# ============================================================
# 4. Output Guardrail Node
# ============================================================
def output_guardrail(state):
    """
    Output guard - runs after the LLM and before sending the message to the customer.
    Validates that any prices mentioned in the response match actual search results.
    """
    messages = state["messages"]
    if not messages:
        return {}
        
    last_message = messages[-1]
    if not getattr(last_message, "content", None) or getattr(last_message, "tool_calls", None):
        return {}
        
    # Trim memory window to match chatbot context (avoid stale price hallucinations)
    if len(messages) > 14:
        recent_messages = messages[-14:]
    else:
        recent_messages = messages
        
    ai_text = last_message.content
    
    # Skip guardrail during closing stage (to avoid blocking phone numbers or order IDs)
    if state.get("funnel_stage") == "closing":
        return {}
        
    import re
    # Extract prices mentioned by the model in its response
    # Exclude numbers starting with 0 (phone numbers like 059) since prices don't start with 0
    price_pattern = r'(?:سعر|بـ|سعره)\s*([1-9]\d*(?:,\d+)?)\s*(?:شيكل|شاقل)?|([1-9]\d*(?:,\d+)?)\s*(?:شيكل|شاقل|شيقل)'
    matches = re.findall(price_pattern, ai_text)
    
    mentioned_numbers = []
    for match in matches:
        num_str = match[0] if match[0] else match[1]
        try:
            mentioned_numbers.append(int(num_str.replace(',', '')))
        except:
            pass
            
    if not mentioned_numbers:
        return {}
        
    # Check for price-related keywords
    price_keywords = ["شيكل", "شيكل", "سعر", "بـ", "سعره"]
    has_price_context = any(keyword in ai_text for keyword in price_keywords)
    
    if has_price_context:
        # Extract numbers from ALL search results in the conversation (not just the latest)
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
                
        # Allow the model to quote any number the customer mentioned (for discussing/rejecting it)
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
                        
        # If no search results exist but the model mentioned a price → confirmed hallucination
        if not tool_numbers:
            return {
                "messages": [AIMessage(
                    content="عذراً، صار عندي خربطة بالأسعار. ممكن تعيد طلبك لحتى أتأكد من النظام؟",
                    id=last_message.id
                )]
            }
            
        # Validate each price mentioned by the model
        for num_val in mentioned_numbers:
            price_valid = False
            for t_val in tool_numbers:
                if num_val == t_val:
                    price_valid = True
                    break
                    
            if not price_valid:
                print(f"[Guardrail Blocked] Hallucinated price: {num_val}")
                return {
                    "messages": [AIMessage(
                        content="عذراً، صار عندي خربطة بالأسعار. ممكن تعيد طلبك لحتى أتأكد من النظام؟",
                        id=last_message.id
                    )]
                }
                
    return {}
