import streamlit as st
import chromadb
from google import genai
import time
import json
import os
import uuid
import fitz
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

# ─── CLIENTS ───────────────────────────────────────────
gemini_client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))
supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

MODELS = ["gemini-2.5-flash", "gemini-2.0-flash", "gemini-2.0-flash-lite"]

# ─── GEMINI ────────────────────────────────────────────
def call_gemini(prompt):
    for model in MODELS:
        try:
            response = gemini_client.models.generate_content(
                model=model, contents=prompt)
            return response.text
        except Exception as e:
            if "503" in str(e) or "429" in str(e):
                time.sleep(3)
                continue
            return None
    return None

# ─── CHROMADB ──────────────────────────────────────────
@st.cache_resource
def load_chromadb():
    chroma = chromadb.Client()
    col = chroma.get_or_create_collection("arthmitra")
    try:
        rows = supabase.table("transactions").select("*").execute().data
        for row in rows:
            try:
                col.add(
                    documents=[row["document"]],
                    metadatas=[{"amount": row["amount"],
                                "category": row["category"],
                                "type": row["type"],
                                "date": row["date"]}],
                    ids=[row["id"]]
                )
            except:
                pass
    except:
        pass
    return col

collection = load_chromadb()

# ─── DATABASE ──────────────────────────────────────────
def get_summary():
    """Get accurate totals directly from Supabase"""
    try:
        rows = supabase.table("transactions").select("*").execute().data
        income, expense, cats = 0, 0, {}
        for r in rows:
            if r["type"] == "income":
                income += r["amount"]
            else:
                expense += r["amount"]
                cats[r["category"]] = cats.get(r["category"], 0) + r["amount"]
        return income, expense, cats
    except:
        return 0, 0, {}

def save_transaction(description, amount, category, txn_type, date, document):
    """Save to both Supabase and ChromaDB"""
    txn_id = str(uuid.uuid4())
    supabase.table("transactions").insert({
        "id": txn_id,
        "description": description,
        "amount": float(amount),
        "category": category,
        "type": txn_type,
        "date": date,
        "document": document
    }).execute()
    try:
        collection.add(
            documents=[document],
            metadatas=[{"amount": float(amount), "category": category,
                        "type": txn_type, "date": date}],
            ids=[txn_id]
        )
    except:
        pass
    return txn_id

# ─── CATEGORIZATION ────────────────────────────────────
def categorize(description):
    desc = description.lower()
    if any(k in desc for k in ["swiggy", "zomato", "dominos", "canteen", "food", "restaurant"]):
        return "food"
    elif any(k in desc for k in ["bus", "uber", "ola", "metro", "auto", "fuel"]):
        return "transport"
    elif any(k in desc for k in ["college", "book", "stationery", "library", "course"]):
        return "education"
    elif any(k in desc for k in ["amazon", "flipkart", "myntra", "shopping", "mall"]):
        return "shopping"
    elif any(k in desc for k in ["netflix", "spotify", "movie", "fest", "game"]):
        return "entertainment"
    elif any(k in desc for k in ["gym", "medical", "pharmacy", "doctor", "hospital"]):
        return "health"
    elif any(k in desc for k in ["salary", "pocket money", "neft", "freelance", "deposit"]):
        return "income"
    else:
        return "other"

# ─── PDF PARSER ────────────────────────────────────────
def parse_pdf(uploaded_file):
    with open("temp.pdf", "wb") as f:
        f.write(uploaded_file.read())
    doc = fitz.open("temp.pdf")
    text = "".join(page.get_text() for page in doc)
    doc.close()

    prompt = f"""
Extract all transactions from this bank statement.
Return ONLY a JSON array:
[{{"date": "DD-Mon-YY", "description": "...", "amount": 000, "type": "expense or income"}}]
Amount always positive. Type exactly "expense" or "income".
Text: {text}
"""
    result = call_gemini(prompt)
    if result:
        try:
            result = result.replace("```json", "").replace("```", "").strip()
            return json.loads(result)
        except:
            return None
    return None

# ─── AI CHAT ───────────────────────────────────────────
def detect_intent(message):
    result = call_gemini(f"""
Respond with ONE word only.
Message: "{message}"
If recording a transaction (spending/receiving money): STORE
If asking a question or advice: ANSWER
""")
    return result.strip().upper() if result else "ANSWER"

def extract_transaction(message):
    result = call_gemini(f"""
Extract transaction from this message. Return ONLY valid JSON:
{{"description": "...", "amount": 000, "category": "food/transport/education/shopping/entertainment/health/other", "type": "expense or income"}}
Message: "{message}"
""")
    if result:
        try:
            result = result.replace("```json", "").replace("```", "").strip()
            return json.loads(result)
        except:
            return None
    return None

def get_ai_answer(question, income, expense, categories):
    """Use Supabase totals for accuracy + RAG for context"""
    results = collection.query(query_texts=[question],
                               n_results=min(5, collection.count())) if collection.count() > 0 else None
    context = "\n".join(results['documents'][0]) if results else "No transactions yet"

    balance = income - expense
    cat_summary = "\n".join([f"- {k}: ₹{v:,.0f}" for k, v in categories.items()])

    prompt = f"""
You are ArthMitra, personal AI CA for Indian students.

ACCURATE FINANCIAL SUMMARY:
- Total Income: ₹{income:,.0f}
- Total Expenses: ₹{expense:,.0f}
- Current Balance: ₹{balance:,.0f}
- Spending by category:
{cat_summary}

RECENT TRANSACTION DETAILS:
{context}

User question: {question}
Answer in 2-3 lines. Be specific with numbers. Be friendly and direct.
"""
    return call_gemini(prompt)

# ─── UI ────────────────────────────────────────────────
st.set_page_config(page_title="ArthMitra", page_icon="💰", layout="centered")

st.markdown("""
<style>
.main-header {
    text-align: center;
    padding: 20px;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    border-radius: 15px;
    color: white;
    margin-bottom: 20px;
}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="main-header">
    <h1>💰 ArthMitra</h1>
    <p>Your Personal AI Chartered Accountant</p>
</div>
""", unsafe_allow_html=True)

# ─── SIDEBAR ───────────────────────────────────────────
income, expense, categories = get_summary()
balance = income - expense

with st.sidebar:
    st.markdown("### 📊 Financial Summary")
    st.metric("💵 Total Income", f"₹{income:,.0f}")
    st.metric("💸 Total Expenses", f"₹{expense:,.0f}")
    st.metric("💰 Balance", f"₹{balance:,.0f}")

    if categories:
        st.markdown("### 📂 By Category")
        for cat, amt in sorted(categories.items(), key=lambda x: x[1], reverse=True):
            st.markdown(f"**{cat.title()}**: ₹{amt:,.0f}")

    st.markdown("### ⚙️ My Profile")
    monthly_budget = st.number_input("Monthly Budget (₹)", value=5000, step=500)
    upcoming_expense = st.text_input("Upcoming Big Expense", "College fees ₹15000 in 3 weeks")

# ─── PDF UPLOAD ────────────────────────────────────────
st.markdown("### 📄 Upload Bank Statement")
uploaded_file = st.file_uploader("Upload PDF", type="pdf")

if uploaded_file and st.button("🔍 Process Statement"):
    with st.spinner("Reading your bank statement..."):
        transactions = parse_pdf(uploaded_file)
        if transactions:
            stored = 0
            for txn in transactions:
                try:
                    cat = categorize(txn["description"])
                    doc = f"{'Received' if txn['type'] == 'income' else 'Spent'} ₹{txn['amount']} on {txn['description']} on {txn['date']}"
                    save_transaction(txn["description"], txn["amount"],
                                     cat, txn["type"], txn["date"], doc)
                    stored += 1
                except:
                    pass
            st.success(f"✅ Imported {stored} transactions!")
            st.rerun()
        else:
            st.error("Could not parse. Try again.")

st.divider()

# ─── CHAT ──────────────────────────────────────────────
st.markdown("### 💬 Chat with ArthMitra")

if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant",
         "content": "Namaste! 🙏 I'm ArthMitra. Tell me what you spent, or ask anything about your finances!"}
    ]

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("e.g. 'I spent ₹200 on groceries' or 'how am I doing this month?'"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            intent = detect_intent(prompt)

            if intent == "STORE":
                data = extract_transaction(prompt)
                if data:
                    doc = f"{'Received' if data['type'] == 'income' else 'Spent'} ₹{data['amount']} on {data['description']}"
                    save_transaction(data["description"], data["amount"],
                                     data.get("category", "other"),
                                     data["type"], "today", doc)
                    response_text = f"✅ Recorded: {doc}"
                else:
                    response_text = "I couldn't understand that. Can you rephrase?"
            else:
                income, expense, categories = get_summary()
                response_text = get_ai_answer(prompt, income, expense, categories) or "Having trouble connecting. Try again!"

            st.markdown(response_text)
            st.session_state.messages.append(
                {"role": "assistant", "content": response_text})
    st.rerun()