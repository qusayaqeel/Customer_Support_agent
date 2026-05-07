# Project State (حالة المشروع)

## الرؤية العامة (Project Vision)
مساعد دعم فني (Customer Support Agent) لمتجر إلكترونيات، يتحدث بشخصية فلسطينية ودودة (أبو العبد). يعتمد المشروع حالياً على معمارية **LangGraph (State Machine)** لضمان مسار آمن للمحادثات، منع الهلوسة، ومنع تسريب الأكواد (Prompt Injection & Code Leaking).

## التقنيات المستخدمة (Tech Stack)
- **النموذج الذكي**: `Llama 3` (عبر `Groq API` لسرعته الفائقة ودعمه للـ Tool Calling).
- **التحكم بالمسار (Orchestration)**: `LangGraph` و `LangChain`.
- **قاعدة البيانات المتجهة (Vector DB)**: `ChromaDB` (للبحث بأسلوب RAG).
- **قاعدة البيانات العادية**: `SQLite` (لحفظ بيانات الطلبات).
- **الواجهة الخلفية (Backend)**: `FastAPI` (جاهز لاستقبال Telegram Webhooks).
- **منهجية العمل**: `TDD` مع اختبارات باستخدام `pytest`.

---

## ما تم إنجازه (Completed Work)
1. **الأساسيات (Core & DB)**: 
   - دوال البحث `search_products` وحفظ الطلبات `save_order` تعمل وتم اختبارها.
2. **الانتقال إلى LangGraph (الخطوات الحالية)**:
   - **الخطوة 1:** تم بناء الكائن المركزي للحالة (`agent/state.py`).
   - **الخطوة 2:** تم تعريف الأدوات (Tools) بشكل نظيف باستخدام مزخرف `@tool` الخاص بـ LangChain لتوليد الـ JSON تلقائياً (`agent/tools.py`).
   - **تنظيف المشروع:** تم مسح ملفات الـ Cache والملفات المؤقتة وإضافتها لملف `.gitignore` للحفاظ على نظافة الـ Repository.

---

## نقطة الانطلاق القادمة (Next Step)
- **الخطوة 3:** تعريف الـ Nodes (العُقد) في مسار `LangGraph` (إنشاء ملف `agent/nodes.py`) والتي ستتضمن عقدة المحادثة `chatbot_node` وعقدة الأدوات `tools_node`.

---

## الهيكلية الحالية للملفات (Project Structure)
```text
Customer_Support_agent/
├── agent/                  # معمارية LangGraph الذكية (العمل الحالي هنا)
│   ├── __init__.py
│   ├── state.py            # حالة النظام (State)
│   └── tools.py            # الأدوات المعرفة بـ LangChain
├── api/                    # بوابات الـ FastAPI (تستقبل رسائل تيليجرام)
├── core/                   # المنطق الأساسي القديم والـ RAG
├── db/                     # قواعد البيانات (SQLite)
├── data/                   # بيانات المنتجات (JSON)
├── tests/                  # ملفات اختبار الـ TDD
└── .gitignore              # ملفات التجاهل (الآن يحمي قواعد البيانات والـ Cache)
```
