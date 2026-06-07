import streamlit as st
import chromadb
from google import genai
import time
import json
import os
from dotenv import load_dotenv

load_dotenv()

# Page config
st.set_page_config(
    page_title="ArthMitra",
    page_icon="💰",
    layout="centered"
)

# Custom CSS
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
    .metric-card {
        background: #f8f9fa;
        padding: 15px;
        border-radius: 10px;
        border-left: 4px solid #667eea;
        margin: 5px 0;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown("""
<div class="main-header">
    <h1>💰 ArthMitra</h1>
    <p>Your Personal AI Chartered Accountant</p>
</div>
""", unsafe_allow_html=True)

# Setup
@st.cache_resource
def setup():
    api_key = os.getenv("GOOGLE_API_KEY")
    client = genai.Client(api_key=api_key)
    chroma_client = chromadb.PersistentClient(path="./arthmitra_memory")
    collection = chroma_client.get_or_create_collection(name="arthmitra_ui")

    # Add starting transactions
    transactions = [
        ("Swiggy food delivery", 350, "food", "expense"),
        ("Dominos pizza", 280, "food", "expense"),
        ("Bus fare", 200, "transport", "expense"),
        ("College canteen", 150, "food", "expense"),
        ("Stationery", 100, "education", "expense"),
        ("Amazon earphones", 1200, "shopping", "expense"),
        ("Pocket money from dad", 5000, "income", "income"),
    ]

    for i, (desc, amount, category, txn_type) in enumerate(transactions):
        try:
            collection.add(
                documents=[f"{'Received' if txn_type == 'income' else 'Spent'} ₹{amount} on {desc}"],
                metadatas=[{"amount": amount, "category": category, "type": txn_type}],
                ids=[f"ui_txn_{i}"]
            )
        except:
            pass

    return client, collection

client, collection = setup()

MODELS = ["gemini-2.5-flash", "gemini-2.0-flash", "gemini-2.0-flash-lite"]

def call_gemini(prompt):
    for model in MODELS:
        try:
            response = client.models.generate_content(
                model=model,
                contents=prompt
            )
            return response.text
        except Exception as e:
            if "503" in str(e) or "429" in str(e):
                time.sleep(3)
                continue
            else:
                return None
    return None

def detect_intent(message):
    prompt = f"""
Analyze this message and respond with ONLY one word.
Message: "{message}"
If the user is recording a transaction (spending or receiving money), respond: STORE
If the user is asking a question or seeking advice, respond: ANSWER
Only respond with STORE or ANSWER. Nothing else.
"""
    result = call_gemini(prompt)
    if result:
        return result.strip().upper()
    return "ANSWER"

def extract_transaction(message):
    prompt = f"""
Extract transaction details from this message and respond ONLY with valid JSON.
Message: "{message}"
Respond with exactly this format:
{{"description": "what was bought/received", "amount": 000, "category": "food/transport/education/shopping/income/other", "type": "expense or income"}}
No extra text. Just the JSON.
"""
    result = call_gemini(prompt)
    if result:
        try:
            result = result.replace("```json", "").replace("```", "").strip()
            return json.loads(result)
        except:
            return None
    return None

def get_financial_summary():
    try:
        all_docs = collection.get()
        total_expense = 0
        total_income = 0
        categories = {}

        for i, metadata in enumerate(all_docs['metadatas']):
            amount = metadata.get('amount', 0)
            txn_type = metadata.get('type', 'expense')
            category = metadata.get('category', 'other')

            if txn_type == 'income':
                total_income += amount
            else:
                total_expense += amount
                categories[category] = categories.get(category, 0) + amount

        return total_income, total_expense, categories
    except:
        return 0, 0, {}

# Sidebar — Financial Summary
with st.sidebar:
    st.markdown("### 📊 Financial Summary")

    total_income, total_expense, categories = get_financial_summary()
    balance = total_income - total_expense

    st.metric("💵 Total Income", f"₹{total_income:,}")
    st.metric("💸 Total Expenses", f"₹{total_expense:,}")
    st.metric("💰 Balance", f"₹{balance:,}",
              delta=f"₹{balance:,}" if balance > 0 else f"-₹{abs(balance):,}")

    st.markdown("### 📂 Spending by Category")
    for cat, amount in sorted(categories.items(), key=lambda x: x[1], reverse=True):
        st.markdown(f"""
        <div class="metric-card">
            <b>{cat.title()}</b>: ₹{amount:,}
        </div>
        """, unsafe_allow_html=True)

    st.markdown("### ⚠️ Upcoming")
    st.error("College Fees: ₹15,000 due in 3 weeks")

# Chat interface
st.markdown("### 💬 Chat with ArthMitra")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Namaste! 🙏 I'm ArthMitra, your personal AI CA. Tell me what you spent, or ask me anything about your finances!"}
    ]

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input
if prompt := st.chat_input("Type here... e.g. 'I spent ₹200 on groceries'"):

    # Add user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Process
    with st.chat_message("assistant"):
        with st.spinner("ArthMitra is thinking..."):

            intent = detect_intent(prompt)

            if intent == "STORE":
                data = extract_transaction(prompt)
                if data:
                    import uuid
                    txn_id = f"txn_{uuid.uuid4().hex[:8]}"
                    doc = f"{'Received' if data['type'] == 'income' else 'Spent'} ₹{data['amount']} on {data['description']}"
                    collection.add(
                        documents=[doc],
                        metadatas=[{
                            "amount": data["amount"],
                            "category": data["category"],
                            "type": data["type"]
                        }],
                        ids=[txn_id]
                    )
                    response_text = f"✅ Recorded: {doc}\n\nYour {data['category']} spending has been updated!"
                else:
                    response_text = "I couldn't understand that transaction. Could you rephrase it?"
            else:
                results = collection.query(
                    query_texts=[prompt],
                    n_results=min(6, collection.count())
                )
                context = "\n".join(results['documents'][0])

                ai_prompt = f"""
You are ArthMitra, personal AI CA for Indian students.
User's recent transactions:
{context}

Monthly budget: ₹5000
College fees due in 3 weeks: ₹15000

Question: {prompt}
Reply in 2-3 lines. Be specific with numbers. Be friendly and direct.
"""
                response_text = call_gemini(ai_prompt) or "Having trouble connecting. Please try again!"

            st.markdown(response_text)
            st.session_state.messages.append({"role": "assistant", "content": response_text})

    # Refresh sidebar stats
    st.rerun()