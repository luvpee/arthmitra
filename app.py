import streamlit as st
from auth import show_login_page, sign_out
from database import load_chromadb, get_summary, save_transaction
from ai import detect_intent, extract_transaction, get_ai_answer
from pdf_parser import parse_pdf
from utils import categorize

st.set_page_config(page_title="ArthMitra", page_icon="💰", layout="centered")

if "user" not in st.session_state:
    st.session_state.user = None

if st.session_state.user is None:
    show_login_page()
else:
    user_id = st.session_state.user.id

    if "collection" not in st.session_state:
        st.session_state.collection = load_chromadb(user_id)

    collection = st.session_state.collection

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

    income, expense, categories = get_summary(user_id)
    balance = income - expense

    with st.sidebar:
        st.markdown(f"### 👤 {st.session_state.user.email}")
        if st.button("Logout", use_container_width=True):
            sign_out()

        st.divider()
        st.markdown("### 📊 Financial Summary")
        st.metric("💵 Total Income", f"₹{income:,.0f}")
        st.metric("💸 Total Expenses", f"₹{expense:,.0f}")
        st.metric("💰 Balance", f"₹{balance:,.0f}")

        if categories:
            st.markdown("### 📂 By Category")
            for cat, amt in sorted(categories.items(),
                                   key=lambda x: x[1], reverse=True):
                st.markdown(f"**{cat.title()}**: ₹{amt:,.0f}")

        st.markdown("### ⚙️ My Profile")
        st.number_input("Monthly Budget (₹)", value=5000, step=500)
        st.text_input("Upcoming Expense", "College fees ₹15000")

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
                        save_transaction(user_id, collection,
                                         txn["description"], txn["amount"],
                                         cat, txn["type"], txn["date"], doc)
                        stored += 1
                    except:
                        pass
                st.success(f"✅ Imported {stored} transactions!")
                st.session_state.collection = load_chromadb(user_id)
                st.rerun()
            else:
                st.error("Could not parse. Try again.")

    st.divider()

    st.markdown("### 💬 Chat with ArthMitra")

    if "messages" not in st.session_state:
        st.session_state.messages = [
            {"role": "assistant",
             "content": "Namaste! 🙏 I'm ArthMitra. Tell me what you spent, or ask anything about your finances!"}
        ]

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("e.g. 'I spent ₹200 on groceries'"):
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
                        save_transaction(user_id, collection,
                                         data["description"], data["amount"],
                                         data.get("category", "other"),
                                         data["type"], "today", doc)
                        response_text = f"✅ Recorded: {doc}"
                    else:
                        response_text = "I couldn't understand that. Can you rephrase?"
                else:
                    income, expense, categories = get_summary(user_id)
                    response_text = get_ai_answer(
                        prompt, collection, income, expense, categories
                    ) or "Having trouble connecting. Try again!"

                st.markdown(response_text)
                st.session_state.messages.append(
                    {"role": "assistant", "content": response_text})
        st.rerun()