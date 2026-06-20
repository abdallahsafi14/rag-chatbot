from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_groq import ChatGroq
from dotenv import load_dotenv
import uvicorn
import os

# ─── تحميل متغيرات البيئة ────────────────────────────────────────────────────
load_dotenv()
print("[STARTUP] ✅ تم تحميل متغيرات البيئة من .env")

# ─── إعدادات المسارات ─────────────────────────────────────────────────────────
CHROMA_PATH = r"chroma_db"
HOST        = "0.0.0.0"
PORT        = int(os.environ.get("PORT", 8000))

# ─── تحميل نموذج الـ Embeddings ──────────────────────────────────────────────
print("[STARTUP] ⏳ جاري تحميل نموذج الـ Embeddings...")
embeddings_model = HuggingFaceEmbeddings(
    model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
)
print("[STARTUP] ✅ تم تحميل نموذج الـ Embeddings بنجاح")

# ─── تهيئة Groq LLM ──────────────────────────────────────────────────────────
print("[STARTUP] ⏳ جاري تهيئة Groq LLM...")
llm = ChatGroq(temperature=0.4, model="llama-3.3-70b-versatile", max_tokens=1024)
print("[STARTUP] ✅ تم تهيئة Groq LLM بنجاح")

# ─── الاتصال بـ ChromaDB ──────────────────────────────────────────────────────
print(f"[STARTUP] ⏳ جاري الاتصال بـ ChromaDB في المسار: {CHROMA_PATH}")
vector_store = Chroma(
    collection_name="example_collection",
    embedding_function=embeddings_model,
    persist_directory=CHROMA_PATH,
)
retriever = vector_store.as_retriever(search_kwargs={"k": 4})
print("[STARTUP] ✅ تم الاتصال بـ ChromaDB بنجاح")

# ─── تعريف تطبيق FastAPI ─────────────────────────────────────────────────────
app = FastAPI(
    title="RAG Chatbot API",
    description="بوت RAG عربي يعمل كـ microservice للتكامل مع NestJS",
    version="1.0.0",
)
print("[STARTUP] ✅ تم إنشاء تطبيق FastAPI")


# ─── نماذج البيانات (Pydantic) ────────────────────────────────────────────────
class ChatRequest(BaseModel):
    """
    الطلب الوارد من الباك اند (أو Postman للاختبار).
    message : نص سؤال المستخدم
    history : سجل المحادثة السابقة (اختياري)
    """
    message: str
    history: list = []


class ChatResponse(BaseModel):
    """
    الرد الذي يُعاد إلى الباك اند.
    reply   : نص إجابة البوت
    sources : عدد المقاطع التي استُخدمت من ChromaDB
    """
    reply: str
    # sources: int


# ─── Endpoint: فحص الصحة ──────────────────────────────────────────────────────
@app.get("/health")
def health_check():
    """
    يُستخدم للتحقق من أن الخدمة شغّالة.
    جرّبه في Postman: GET http://localhost:8000/health
    """
    print("[HEALTH] طلب فحص صحة الخدمة")
    return {"status": "ok", "service": "RAG Chatbot"}


# ─── Endpoint: إرسال رسالة والحصول على رد ────────────────────────────────────
@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    """
    الـ endpoint الرئيسي. يستقبل رسالة ويعيد رداً.

    مثال Postman:
      POST http://localhost:8000/chat
      Body (JSON):
        {
          "message": "ما هو نظام IAM؟",
          "history": []
        }
    """
    print(f"\n{'='*60}")
    print(f"[CHAT] 📨 طلب جديد وصل")
    print(f"[CHAT] 📝 الرسالة: {request.message}")
    print(f"[CHAT] 📜 طول سجل المحادثة: {len(request.history)} رسالة سابقة")

    # ── التحقق من أن الرسالة ليست فارغة ──────────────────────────────────────
    if not request.message.strip():
        print("[CHAT] ⚠️  الرسالة فارغة — تم رفض الطلب")
        raise HTTPException(status_code=400, detail="الرسالة لا يمكن أن تكون فارغة")

    # ── استرجاع المقاطع ذات الصلة من ChromaDB ────────────────────────────────
    print(f"[RETRIEVER] ⏳ جاري البحث في ChromaDB...")
    try:
        docs = retriever.invoke(request.message)
    except Exception as e:
        print(f"[RETRIEVER] ❌ خطأ أثناء البحث في ChromaDB: {e}")
        raise HTTPException(status_code=500, detail=f"خطأ في ChromaDB: {str(e)}")

    print(f"[RETRIEVER] ✅ تم استرجاع {len(docs)} مقطع")
    for i, doc in enumerate(docs):
        print(f"[RETRIEVER]   مقطع {i+1}: {doc.page_content[:80].strip()}...")

    # ── بناء محتوى السياق من المقاطع المسترجعة ───────────────────────────────
    knowledge = ""
    for doc in docs:
        knowledge += doc.page_content[:600] + "\n\n"

    if not knowledge.strip():
        print("[RETRIEVER] ⚠️  لم يُعثر على أي محتوى ذي صلة في ChromaDB")

    # ── بناء الـ Prompt ────────────────────────────────────────────────────────
    rag_prompt = f"""
    أنت مساعد ذكي متخصص تجيب على أسئلة المستخدمين بناءً على محتوى وثيقة رسمية.

    **قواعد الإجابة:**
    - أجب باللغة العربية الفصحى بأسلوب واضح ومنظم.
    - اعتمد حصراً على المعلومات المتاحة أدناه ولا تضف معلومات من عندك.
    - إذا كان السؤال تحية أو خارج نطاق الوثيقة، رد بإيجاز ووجّه المستخدم لطرح سؤال متعلق بالوثيقة.
    - إذا لم تجد الإجابة في المعلومات المتاحة قل: "لا تتوفر لديّ معلومات كافية حول هذا الموضوع في الوثيقة."
    - نظّم إجابتك بنقاط أو فقرات عند الحاجة.
    - لا تذكر أنك تعتمد على وثيقة أو مصدر معين.

    السؤال: {request.message}

    سجل المحادثة: {request.history}

    المعلومات المتاحة:
    {knowledge}
    """

    # ── إرسال الـ Prompt إلى Groq وتجميع الرد ────────────────────────────────
    print(f"[LLM] ⏳ جاري إرسال الطلب إلى Groq...")
    try:
        full_reply = ""
        for chunk in llm.stream(rag_prompt):
            full_reply += chunk.content
    except Exception as e:
        print(f"[LLM] ❌ خطأ أثناء الاتصال بـ Groq: {e}")
        raise HTTPException(status_code=502, detail=f"خطأ في Groq: {str(e)}")

    print(f"[LLM] ✅ تم استلام الرد من Groq")
    print(f"[LLM] 📤 الرد ({len(full_reply)} حرف): {full_reply[:120].strip()}...")
    print(f"{'='*60}\n")

    return ChatResponse(reply=full_reply)


# ─── تشغيل الخادم ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print(f"\n[STARTUP] 🚀 جاري تشغيل الخادم على http://{HOST}:{PORT}")
    uvicorn.run(app, host=HOST, port=PORT)