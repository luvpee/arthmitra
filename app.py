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
        # ── Profile Section ──
        with st.expander("👤 My Profile", expanded=True):
            st.markdown(f"**{st.session_state.user.email}**")
            monthly_budget = st.number_input(
                "Monthly Budget (₹)",
                value=5000,
                step=500,
                key="monthly_budget"
            )
            upcoming_expense = st.text_input(
                "Upcoming Big Expense",
                "College fees ₹15000 in 3 weeks",
                key="upcoming_expense"
            )
            if st.button("Logout", use_container_width=True):
                sign_out()

        st.divider()

        # ── Financial Summary ──
        st.markdown("### 📊 Financial Summary")

        budget_used = (expense / monthly_budget * 100) if monthly_budget > 0 else 0

        st.metric("💵 Total Income", f"₹{income:,.0f}")
        st.metric("💸 Total Expenses", f"₹{expense:,.0f}",
                delta=f"{budget_used:.0f}% of budget used")
        st.metric("💰 Balance", f"₹{balance:,.0f}",
                delta=f"₹{balance:,.0f}" if balance >= 0 else f"-₹{abs(balance):,.0f}")

        # Budget progress bar
        st.markdown("**Budget Usage:**")
        progress = min(budget_used / 100, 1.0)
        st.progress(progress)
        if budget_used > 90:
            st.error(f"⚠️ {budget_used:.0f}% of budget used!")
        elif budget_used > 70:
            st.warning(f"📊 {budget_used:.0f}% of budget used")
        else:
            st.success(f"✅ {budget_used:.0f}% of budget used")

        st.divider()

        # ── Spending Breakdown ──
        if categories:
            st.markdown("### 📂 Spending Breakdown")
            for cat, amt in sorted(categories.items(),
                                key=lambda x: x[1], reverse=True):
                pct = (amt / expense * 100) if expense > 0 else 0
                st.markdown(f"**{cat.title()}** — ₹{amt:,.0f} ({pct:.0f}%)")

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
                        save_transaction(
                            user_id,
                            collection,
                            txn["description"],
                            txn["amount"],
                            cat,
                            txn["type"],
                            txn["date"],
                            doc,
                        )
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
            {
                "role": "assistant",
                "content": "Namaste! 🙏 I'm ArthMitra. Tell me what you spent, or ask anything about your finances!",
            }
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
                try:
                    from agents import process_message
                    income, expense, categories = get_summary(user_id)
                    response_text, agent_used, alerts = process_message(
                        prompt, user_id, collection, income, expense, categories
                    )
                    if not response_text:
                        raise Exception("No response")
                    st.caption(f"Handled by: {agent_used}")
                except Exception as e:
                    from ai import detect_intent, extract_transaction, get_ai_answer
                    intent = detect_intent(prompt)
                    if intent == "STORE":
                        data = extract_transaction(prompt)
                        if data:
                            doc = f"{'Received' if data['type'] == 'income' else 'Spent'} ₹{data['amount']} on {data['description']}"
                            save_transaction(
                                user_id,
                                collection,
                                data["description"],
                                data["amount"],
                                data.get("category", "other"),
                                data["type"],
                                "today",
                                doc,
                            )
                            response_text = f"✅ Recorded: {doc}"
                        else:
                            response_text = "I couldn't understand that. Can you rephrase?"
                    else:
                        income, expense, categories = get_summary(user_id)
                        response_text = (
                            get_ai_answer(
                                prompt, collection, income, expense, categories
                            )
                            or "Having trouble connecting. Try again!"
                        )

                st.markdown(response_text)
                st.session_state.messages.append(
                    {"role": "assistant", "content": response_text}
                )

        st.rerun()