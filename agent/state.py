from typing import TypedDict, Annotated, Sequence
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages

class AgentState(TypedDict):
    """
    حالة النظام المركزية - تتنقل بين كل العُقد في الـ Graph.
    
    تم ترقيتها من مجرد "ذاكرة رسائل" إلى State Machine كامل يتتبع:
    - messages: سجل المحادثة الكامل
    - funnel_stage: المرحلة الحالية في قمع المبيعات (Sales Funnel)
    - guardrail_passed: هل الرسالة آمنة ومرتبطة بعمل المتجر
    """
    # سجل المحادثة - الـ Reducer يضمن تراكم الرسائل بدون مسح
    messages: Annotated[Sequence[BaseMessage], add_messages]
    
    # مرحلة قمع المبيعات (Sales Funnel Stage)
    # greeting   = ترحيب واستكشاف أولي
    # discovery  = جمع متطلبات العميل (الاستخدام + الميزانية)
    # pitching   = عرض المنتجات من نتائج البحث
    # closing    = تأكيد الشراء وجمع بيانات الطلب
    funnel_stage: str
    
    # نتيجة فحص الحماية - هل الرسالة الأخيرة آمنة أم لا
    guardrail_passed: bool
