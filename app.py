import streamlit as st
import chromadb
from google import genai
import time
import json
import os
import uuid
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

# Initialize clients
GEMINI_KEY = os.getenv("GOOGLE_API_KEY")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

gemini_client = genai.Client(api_key=GEMINI_KEY)
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

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
    chroma_client = chromadb.Client()  # in-memory chromadb
    collection = chroma_client.get_or_create_collection(name="arthmitra_ui")

    # Load existing transactions from Supabase into ChromaDB
    try:
        response = supabase.table("transactions").select("*").execute()
        transactions = response.data

        if transactions:
            for txn in transactions:
                try:
                    collection.add(
                        documents=[txn["document"]],
                        metadatas=[{
                            "amount": txn["amount"],
                            "category": txn["category"],
                            "type": txn["type"],
                            "date": txn["date"]
                        }],
                        ids=[txn["id"]]
                    )
                except:
                    pass
            print(f"✅ Loaded {len(transactions)} transactions from Supabase")
        else:
            print("📭 No existing transactions found")

    except Exception as e:
        print(f"Error loading from Supabase: {e}")

    return gemini_client, collection

client, collection = setup()

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

# PDF Upload Section
st.markdown("### 📄 Upload Bank Statement")

uploaded_file = st.file_uploader(
    "Upload your bank statement PDF",
    type="pdf",
    help="We'll automatically extract and store all your transactions"
)

if uploaded_file is not None:
    if st.button("🔍 Process Statement"):
        with st.spinner("Reading your bank statement..."):

            # Save uploaded file temporarily
            import tempfile
            import fitz
            import uuid

            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                tmp.write(uploaded_file.read())
                tmp_path = tmp.name

            # Extract text
            doc = fitz.open(tmp_path)
            raw_text = ""
            for page in doc:
                raw_text += page.get_text()
            doc.close()

            # Extract transactions with Gemini
            parse_prompt = f"""
You are a bank statement parser. Extract all transactions from this text.
Return ONLY a JSON array with this format:
[
  {{"date": "DD-Mon-YY", "description": "description", "amount": 000, "type": "expense or income"}},
]
Amount always positive. Type is exactly "expense" or "income".
Text:
{raw_text}
"""
            result = call_gemini(parse_prompt)

            if result:
                try:
                    result = result.replace("```json","").replace("```","").strip()
                    transactions = json.loads(result)

                    # Store each transaction
                    stored = 0
                    for txn in transactions:
                        try:
                            food_kw = ["swiggy","zomato","dominos","canteen","food"]
                            transport_kw = ["bus","uber","ola","metro","auto"]
                            education_kw = ["college","book","stationery","library"]
                            shopping_kw = ["amazon","flipkart","myntra","shop"]
                            entertainment_kw = ["netflix","spotify","movie","fest"]
                            health_kw = ["gym","medical","pharmacy","doctor"]

                            desc_lower = txn["description"].lower()
                            if any(k in desc_lower for k in food_kw):
                                category = "food"
                            elif any(k in desc_lower for k in transport_kw):
                                category = "transport"
                            elif any(k in desc_lower for k in education_kw):
                                category = "education"
                            elif any(k in desc_lower for k in shopping_kw):
                                category = "shopping"
                            elif any(k in desc_lower for k in entertainment_kw):
                                category = "entertainment"
                            elif any(k in desc_lower for k in health_kw):
                                category = "health"
                            else:
                                category = "other"

                            doc_text = f"{'Received' if txn['type'] == 'income' else 'Spent'} ₹{txn['amount']} on {txn['description']} on {txn['date']}"
                            txn_id = str(uuid.uuid4())
                            doc_text = f"{'Received' if txn['type'] == 'income' else 'Spent'} ₹{txn['amount']} on {txn['description']} on {txn['date']}"

                            # Save to Supabase permanently
                            supabase.table("transactions").insert({
                                "id": txn_id,
                                "description": txn["description"],
                                "amount": float(txn["amount"]),
                                "category": category,
                                "type": txn["type"],
                                "date": txn["date"],
                                "document": doc_text
                            }).execute()

                            # Also add to ChromaDB for semantic search
                            collection.add(
                                documents=[doc_text],
                                metadatas=[{
                                    "amount": float(txn["amount"]),
                                    "category": category,
                                    "type": txn["type"],
                                    "date": txn["date"]
                                }],
                                ids=[txn_id]
                            )
                            stored += 1
                            
                            
                        except:
                            pass

                    st.success(f"✅ Successfully imported {stored} transactions from your bank statement!")
                    st.rerun()

                except Exception as e:
                    st.error("Could not parse the statement. Please try again.")
            else:
                st.error("Having trouble connecting. Please try again.")

st.divider()

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