# Abu Al-Abd - Smart Store AI Agent
## حالة المشروع (Project State)

### فكرة المشروع
بوت تيليجرام ذكي يعمل كبائع إلكترونيات فلسطيني اسمه "أبو العبد" لمتجر "سمارت ستور".
يستخدم RAG للبحث عن المنتجات وLangGraph كـ State Machine لإدارة مسار المحادثة.

---

### التقنيات المستخدمة (Tech Stack)
| التقنية | الاستخدام |
|---|---|
| **LangGraph** | State Machine لإدارة مسار المحادثة (Nodes + Edges) |
| **LangChain** | LLM Integration + Tool Binding |
| **Groq** | LLM Provider (meta-llama/llama-4-scout-17b-16e-instruct) |
| **ChromaDB** | Vector Database للبحث الدلالي عن المنتجات (RAG) |
| **FastAPI** | API Server + Telegram Webhook |
| **SQLite** | قاعدة بيانات الطلبات |
| **Ngrok** | Tunnel لربط السيرفر المحلي بتيليجرام |

---

### هيكل المشروع (Project Structure)
```
Customer_Support_agent/
├── main.py                  # نقطة الدخول - FastAPI + تهيئة قواعد البيانات
├── requirements.txt         # الاعتمادات
├── .env                     # مفاتيح API (GROQ_API_KEY, TELEGRAM_BOT_TOKEN)
│
├── agent/                   # طبقة الـ AI Agent (LangGraph)
│   ├── state.py             # AgentState: messages + funnel_stage + guardrail_passed
│   ├── nodes.py             # العُقد: input_guardrail → chatbot → output_guardrail
│   ├── graph.py             # المخطط: توصيل العُقد والتوجيه الشرطي
│   └── tools.py             # أدوات LangChain: search_store_products + save_customer_order
│
├── api/
│   └── webhook.py           # Telegram Webhook + session management
│
├── core/
│   ├── rag.py               # ChromaDB: init_vector_store + search_products (Strict RAG)
│   └── agent.py             # [قديم - غير مستخدم] النظام الخطي السابق
│
├── db/
│   └── database.py          # SQLite: init_db + save_order
│
├── data/
│   └── products.json        # كتالوج المنتجات (20 منتج)
│
└── chroma_db/               # قاعدة بيانات المتجهات (يُعاد بناؤها تلقائياً)
```

---

### المعمارية الحالية (Architecture)
```
رسالة تيليجرام
      │
      ▼
  [webhook.py] → يستقبل الرسالة ويحفظ الجلسة
      │
      ▼
  [input_guardrail] → فحص برمجي (Regex): Prompt Injection + Off-Topic
      │
  ┌───┴───┐
  │ آمنة؟ │
  └───┬───┘
   نعم│    لا → رد تلقائي → END
      ▼
  [chatbot] → أبو العبد (LLM + System Prompt + Funnel Stage)
      │
  ┌───┴────┐
  │ أداة؟  │
  └───┬────┘
   نعم│    لا
      ▼      ▼
  [tools] [output_guardrail] → فحص الأسعار والمنتجات → END
      │
      ▼
  [chatbot] → يقرأ نتائج الأداة ويرد
      │
      ▼
  [output_guardrail] → فحص نهائي → END
```

---

### الحالة الحالية (Current Status) ✅
- [x] LangGraph State Machine مع 4 عُقد
- [x] Input Guardrail: حماية من Prompt Injection (Regex)
- [x] Output Guardrail: Active Context State (فحص الأسعار ضد نتائج البحث)
- [x] Strict RAG: فلترة بحسب similarity distance (threshold 1.5)
- [x] Sales Funnel: greeting → discovery → pitching → closing
- [x] System Prompt بلهجة فلسطينية + 8 أقسام
- [x] كتالوج 20 منتج متنوع (هواتف، حواسيب، صوتيات، ساعات، اكسسوارات)
- [x] Tool Output Formatting: إخفاء stock من نتائج البحث
- [x] ChromaDB يُعاد بناؤه من products.json كل مرة (delete + create)

---

### المشاكل المعروفة والتعديلات المطلوبة 🔧

#### مشكلة 1: هلوسة المنتجات (Pre-trained Knowledge Leakage)
**الوصف:** الموديل أحياناً يخترع منتجات غير موجودة في الداتا بيس (مثل Dell Inspiron 3000 بكود p101) أو يقترح منتجات من تصنيفات مختلفة (سأل عن لابتوب فيقترح كيبورد).
**الحالة:** تم بناء Output Guardrail + Strict RAG + قواعد Prompt. بحاجة لاختبار شامل.
**ملفات مرتبطة:** `agent/nodes.py` (output_guardrail), `core/rag.py` (max_distance), `agent/tools.py` (formatting)

#### مشكلة 2: أسلوب الرد غير طبيعي
**الوصف:** الموديل أحياناً يرد بردود طويلة أو يستخدم لهجة مصرية أو فصحى بدل الفلسطينية.
**الحل المقترح:** Few-shot examples في الـ Prompt + Post-processing في webhook.py

#### تعديل 3: تحديث دالة save_customer_order
**الوصف:** الدالة الحالية تأخذ فقط (product_id, name, phone). المطلوب:
- إضافة حقول: المدينة، العنوان، طريقة الدفع
- Validation لرقم التلفون الفلسطيني (يبدأ بـ 059 أو 056، طوله 10 أرقام)
- إرجاع رقم الطلب (Order ID) للعميل
**ملفات مرتبطة:** `agent/tools.py`, `db/database.py`

#### تعديل 4: Structured Output + Telegram Inline Keyboards
**الوصف:** بدلاً من إرسال نص طويل، المطلوب:
- الموديل يرجع JSON منظم (product_id + short_pitch)
- الـ webhook يبني Telegram Inline Keyboard (أزرار "اشتري" و "تفاصيل")
**ملفات مرتبطة:** `api/webhook.py`, `agent/nodes.py`

#### تعديل 5: إدارة الذاكرة (Session Management)
**الوصف:** الجلسات في `user_sessions` (RAM) بدون حد. المطلوب:
- تحديد عدد أقصى للرسائل (آخر 20 رسالة)
- مسح الجلسة بعد 30 دقيقة من عدم النشاط
- التعامل مع أمر /start لإعادة تعيين الجلسة
**ملفات مرتبطة:** `api/webhook.py`

#### تعديل 6: حذف core/agent.py
**الوصف:** ملف قديم من النظام الخطي السابق قبل LangGraph. غير مستخدم حالياً.

---

### متغيرات البيئة المطلوبة (.env)
```
GROQ_API_KEY=gsk_...
TELEGRAM_BOT_TOKEN=...
```

### تشغيل المشروع
```bash
# تثبيت الاعتمادات
pip install -r requirements.txt

# تشغيل السيرفر
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# ربط Ngrok
ngrok http 8000

# تسجيل الـ Webhook في تيليجرام
# https://api.telegram.org/bot<TOKEN>/setWebhook?url=<NGROK_URL>/webhook
```
