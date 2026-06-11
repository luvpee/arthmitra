import streamlit as st
from auth import show_login_page, sign_out
from database import load_chromadb, get_summary, save_transaction
from ai import detect_intent, extract_transaction, get_ai_answer
from pdf_parser import parse_pdf
from utils import categorize
from database import get_user_profile, save_user_profile, get_upcoming_expenses, add_upcoming_expense, delete_upcoming_expense

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

    # ── FETCH DATA BEFORE SIDEBAR ──
    if "profile" not in st.session_state:
        st.session_state.profile = get_user_profile(user_id)
    
    monthly_budget = st.session_state.profile.get("monthly_budget", 5000)
    upcoming_expenses = get_upcoming_expenses(user_id)

    # (Assuming income, expense, categories, and balance are already calculated here)
    
    # ── FETCH DATA BEFORE SIDEBAR ──
    if "profile" not in st.session_state:
        st.session_state.profile = get_user_profile(user_id)
    
    monthly_budget = st.session_state.profile.get("monthly_budget", 5000)
    current_name = st.session_state.profile.get("full_name", "Mitra")
    upcoming_expenses = get_upcoming_expenses(user_id)

    with st.sidebar:
        # ── 1. Clean Profile Section ──
        st.markdown(f"## Hey, {current_name}! 👋")
        st.caption(f"📧 {st.session_state.user.email}")
        if st.button("🚪 Logout", use_container_width=True):
            sign_out()

        st.divider()

        # ── 2. Dedicated Budget Configuration ──
        st.markdown("### 🎯 Budget Planning")
        new_budget = st.number_input(
            "Set Monthly Budget Limit (₹)",
            value=int(monthly_budget),
            step=500,
            key="budget_input"
        )
        if st.button("💾 Update Budget", use_container_width=True, type="secondary"):
            # Update database with the new budget while keeping the same name
            save_user_profile(user_id, new_budget, current_name)
            st.session_state.profile["monthly_budget"] = new_budget
            st.success("Budget limit updated! 🎯")
            st.rerun()

        st.divider()

        # ── 3. Financial Summary ──
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

        # ── 4. Upcoming Expenses Form ──
        st.markdown("### 📅 Upcoming Expenses")
        with st.form("upcoming_expense_form", clear_on_submit=True):
            exp_desc = st.text_input("Item Description", placeholder="e.g., Exam Fees")
            exp_amt = st.number_input("Amount (₹)", min_value=0, step=100)
            exp_date = st.date_input("Due Date")
            if st.form_submit_button("➕ Add Expense"):
                if exp_desc and exp_amt > 0:
                    add_upcoming_expense(user_id, exp_desc, exp_amt, exp_date)
                    st.rerun()

        # Display the list of upcoming expenses with Delete buttons
        if upcoming_expenses:
            for exp in upcoming_expenses:
                col1, col2 = st.columns([4, 1])
                with col1:
                    st.markdown(f"**{exp['description']}**\n₹{exp['amount']:,.0f} | {exp['due_date']}")
                with col2:
                    if st.button("❌", key=f"del_{exp['id']}"):
                        delete_upcoming_expense(exp['id'])
                        st.rerun()
        else:
            st.caption("No upcoming expenses listed.")

        st.divider()

        # ── 5. Spending Breakdown ──
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
                    # Pass all the new variables to the agent
                    response_text, agent_used, alerts = process_message(
                    prompt, user_id, collection, income, expense, categories, monthly_budget, upcoming_expenses
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