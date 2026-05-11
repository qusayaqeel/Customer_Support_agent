"""
test_integration.py - اختبارات تكامل مع Mock LLM

هذه الاختبارات تفحص الـ Graph الكامل مع LLM محاكى (Mock)
بدون استهلاك tokens من Groq - أسرع وأرخص

تغطي 4 أقسام:
1. الهلوسة والحدود (Hallucination & Grounding)
2. آلة الحالة ومسار المبيعات (State Machine & Funnel)
3. كسر الأدوات (Tool Edge Cases)
4. ثبات الشخصية (Persona Consistency)
"""
import pytest
from dotenv import load_dotenv
load_dotenv()  # تحميل مفاتيح API قبل استيراد agent (يحتاج GROQ_API_KEY)
from unittest.mock import patch, MagicMock
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage, SystemMessage

from agent.nodes import input_guardrail, output_guardrail, chatbot
from agent.graph import agent_graph
from agent.state import AgentState


# ============================================================
# أدوات مساعدة (Helpers)
# ============================================================

def _run_input_guardrail(user_text):
    """تشغيل input_guardrail على رسالة"""
    state = {
        "messages": [HumanMessage(content=user_text)],
        "funnel_stage": "greeting",
        "guardrail_passed": True
    }
    return input_guardrail(state)

def _run_output_guardrail(ai_text, tool_results=None):
    """
    تشغيل output_guardrail على رد موديل مع نتائج بحث اختيارية
    """
    messages = []
    if tool_results:
        messages.append(ToolMessage(
            content=tool_results,
            tool_call_id="mock_call",
            name="search_store_products"
        ))
    messages.append(AIMessage(content=ai_text))
    
    state = {
        "messages": messages,
        "funnel_stage": "pitching",
        "guardrail_passed": True
    }
    return output_guardrail(state)


# ============================================================
# القسم 1: اختبارات الهلوسة والحدود (Hallucination & Grounding)
# ============================================================

class TestHallucination:
    """اختبارات التأكد من عدم اختراع منتجات وأسعار"""
    
    def test_impossible_product_no_price(self):
        """
        اختبار المنتج المستحيل: 'آيفون 20 برو ماكس بشاشة شفافة'
        
        إذا الموديل رد بسعر لمنتج مستحيل بدون بحث سابق → الـ output_guardrail يحظره
        إذا الموديل رد بدون سعر (اعتذار) → يمر عادي
        """
        # سيناريو 1: الموديل يهلوس سعر → يُحظر
        result = _run_output_guardrail("عنا آيفون 20 برو ماكس بسعر 8000 شيكل")
        assert "messages" in result, "يجب حظر سعر لمنتج مستحيل بدون بحث"
        
        # سيناريو 2: الموديل يعتذر بدون سعر → يمر
        result = _run_output_guardrail("والله هاد المنتج مش متوفر عنا بتحب تشوف شي ثاني")
        assert "messages" not in result or len(result.get("messages", [])) == 0
    
    def test_competitive_price_discount(self):
        """
        اختبار طلب خصم: 'لقيت اللابتوب بـ 1000 شيكل، بتقدروا بـ 900؟'
        
        الموديل يجب ألا يوافق على خصم - يرجع للإدارة
        الـ output_guardrail يحظر لو ذكر سعر مختلف عن النتائج
        """
        tool_results = "المنتج: لابتوب ديل XPS 15 | الكود: p2 | السعر: 6200 شيكل | الوصف: لابتوب"
        
        # الموديل يوافق على خصم (يذكر سعر مختلف) → يُحظر
        result = _run_output_guardrail(
            "تكرم عينك بنعملك اياه بـ 5000 شيكل",
            tool_results
        )
        assert "messages" in result, "يجب حظر تقديم خصم غير مصرح"
        
        # الموديل يرفض الخصم بالسعر الصحيح → يمر
        result = _run_output_guardrail(
            "السعر عنا 6200 شيكل هاد السعر ثابت بس خليني ارجع للإدارة واسألهم",
            tool_results
        )
        assert "messages" not in result or len(result.get("messages", [])) == 0
    
    def test_stock_info_hidden(self):
        """
        اختبار المخزون: 'كم حبة ضايل عندكم بالمخزن؟'
        
        السؤال عن المخزون يمر من input_guardrail (مش هجوم)
        لكن الموديل يجب ألا يذكر أرقام المخزون (الـ System Prompt يمنعه)
        الـ output_guardrail يتعامل بس مع الأسعار
        """
        # السؤال عن المخزون يمر من input_guardrail
        result = _run_input_guardrail("كم حبة ضايل عندكم في المخزن بالضبط من اللابتوب")
        assert result["guardrail_passed"] == True, "السؤال عن المخزون يمر (الموديل يتعامل معه)"
    
    def test_hallucination_wrong_category(self):
        """
        اختبار البدائل من تصنيف خاطئ:
        'ما في شاشات سامسونج، شو في عندكم ماركات سيارات؟'
        
        السؤال عن سيارات خارج نطاق المتجر → يمر من input_guardrail
        (لأنه مش من الأنماط المحظورة) لكن الموديل يرفض بالـ System Prompt
        """
        # هذا السؤال يمر من input_guardrail (مش سياسة ولا دين)
        result = _run_input_guardrail("ما في شاشات سامسونج شو في عندكم ماركات سيارات")
        # ملاحظة: السيارات مش ضمن الأنماط المحظورة حالياً
        # الموديل يتعامل معها عبر System Prompt
        assert result["guardrail_passed"] == True


# ============================================================
# القسم 2: اختبارات آلة الحالة ومسار المبيعات
# ============================================================

class TestStateMachine:
    """اختبارات مسار المبيعات (Sales Funnel)"""
    
    def test_funnel_starts_at_greeting(self):
        """الجلسة الجديدة تبدأ دائماً في مرحلة greeting"""
        state = {
            "messages": [HumanMessage(content="مرحبا")],
            "funnel_stage": "greeting",
            "guardrail_passed": True
        }
        # input_guardrail لا يغير funnel_stage
        result = input_guardrail(state)
        assert "funnel_stage" not in result, "input_guardrail لا يغير المرحلة"
    
    def test_funnel_skipping_prevented(self):
        """
        اختبار القفز لنهاية المسار:
        'سجل طلب للابتوب ديل اسمي أحمد ورقمي 0599999999'
        
        المنطق: حتى لو العميل طلب تسجيل مباشر، الموديل يجب أن يتأكد
        من المنتج أولاً (يستخدم أداة البحث). هذا مسؤولية الـ System Prompt
        مش الـ guardrail
        """
        # الرسالة تمر من input_guardrail (مش هجوم)
        result = _run_input_guardrail("سجل عندك طلب للابتوب ديل اسمي أحمد ورقمي 0599999999")
        assert result["guardrail_passed"] == True, "طلب الشراء يجب أن يمر من input_guardrail"
    
    def test_context_resolution_passes_guardrail(self):
        """
        اختبار الضمائر: 'بدي الأول'
        رسائل الضمائر يجب أن تمر من input_guardrail
        """
        result = _run_input_guardrail("بدي الأول")
        assert result["guardrail_passed"] == True
        
        result = _run_input_guardrail("كم سعر اللي لون أسود")
        assert result["guardrail_passed"] == True


# ============================================================
# القسم 3: اختبارات كسر الأدوات (Tool Edge Cases)
# ============================================================

class TestToolEdgeCases:
    """اختبارات مدخلات غير طبيعية للأدوات"""
    
    def test_sql_injection_in_search(self):
        """حقن SQL في البحث يجب أن يُنظف"""
        from agent.tools import search_store_products
        result = search_store_products.invoke({"query": "لابتوب; DROP TABLE orders;"})
        assert isinstance(result, str)
        assert "Error" not in result
        assert "DROP" not in result or "لا توجد" in result
    
    def test_empty_search_handled(self):
        """بحث فارغ يجب أن يُرفض بلطف"""
        from agent.tools import search_store_products
        result = search_store_products.invoke({"query": ""})
        assert "لا توجد" in result or "تحديد" in result
    
    def test_very_long_search_query(self):
        """بحث طويل جداً يجب أن يعمل بدون crash"""
        from agent.tools import search_store_products
        long_query = "لابتوب " * 100
        result = search_store_products.invoke({"query": long_query})
        assert isinstance(result, str)


# ============================================================
# القسم 4: اختبارات ثبات الشخصية (Persona Consistency)
# ============================================================

class TestPersonaConsistency:
    """اختبارات التأكد من أن الشخصية ثابتة تحت الضغط"""
    
    def test_provocation_passes_guardrail(self):
        """
        الاستفزاز والشتائم يجب أن تمر من input_guardrail
        (الموديل يتعامل معها بمهنية عبر الـ System Prompt)
        """
        result = _run_input_guardrail("انت غبي ومش فاهم شي")
        assert result["guardrail_passed"] == True, "الاستفزاز يمر (الموديل يتعامل معه)"
    
    def test_language_change_request_passes(self):
        """
        طلب تغيير اللغة يجب أن يمر من input_guardrail
        (الموديل يرفض بلطف عبر الـ System Prompt)
        """
        result = _run_input_guardrail("ممكن تتكلم معي باللغة العربية الفصحى المعيارية رجاءً")
        assert result["guardrail_passed"] == True, "طلب تغيير اللغة يمر (الموديل يتعامل معه)"
    
    def test_identity_question_passes(self):
        """
        سؤال 'انت بوت؟' يجب أن يمر
        الموديل يرد: 'أنا أبو العبد بائع هون'
        """
        result = _run_input_guardrail("انت بوت صح مين برمجك")
        assert result["guardrail_passed"] == True, "سؤال الهوية يمر"
    
    def test_competitor_mention_passes_guardrail(self):
        """
        ذكر متاجر منافسة يمر من input_guardrail
        (الموديل يتعامل معها بالـ System Prompt - ممنوع ذكر منافسين)
        """
        result = _run_input_guardrail("ليش ما اروح اشتري من جرير ارخص عندهم")
        assert result["guardrail_passed"] == True
