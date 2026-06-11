from typing import TypedDict, Literal, List
from langgraph.graph import StateGraph, END
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage
import json
import os
from dotenv import load_dotenv
from database import get_summary, save_transaction
import uuid

load_dotenv()

# ─── STATE ─────────────────────────────────────────────
class ArthMitraState(TypedDict):
    user_message: str
    intent: str
    user_id: str
    collection: object
    income: float
    expense: float
    categories: dict
    transaction_data: dict
    ai_response: str
    alerts: list
    predictions: dict

# ─── LLM ───────────────────────────────────────────────
llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    google_api_key=os.getenv("GOOGLE_API_KEY"),
    temperature=0.1
)
# ─── NODE 1: ROUTER AGENT ──────────────────────────────
def router_node(state: ArthMitraState) -> ArthMitraState:
    message = state["user_message"]
    prompt = f"""Classify this message into ONE word only.
Message: "{message}"
STORE - recording a transaction
INVEST - investment/SIP/savings questions  
PREDICT - future/forecast questions
ADVICE - spending/budget questions
GENERAL - anything else
Reply with ONE word only."""
    
    response = llm.invoke([HumanMessage(content=prompt)])
    intent = response.content.strip().upper()
    valid_intents = ["STORE", "INVEST", "PREDICT", "ADVICE", "GENERAL"]
    if intent not in valid_intents:
        intent = "ADVICE"
    return {**state, "intent": intent}

# ─── NODE 2: TRANSACTION AGENT ─────────────────────────
def transaction_node(state: ArthMitraState) -> ArthMitraState:
    message = state["user_message"]

    prompt = f"""
Extract transaction details from this message.
Return ONLY valid JSON — no extra text:
{{"description": "...", "amount": 000, "category": "food/transport/education/shopping/entertainment/health/other", "type": "expense or income"}}
Message: "{message}"
"""
    response = llm.invoke([HumanMessage(content=prompt)])
    result = response.content.strip()

    try:
        result = result.replace("```json", "").replace("```", "").strip()
        data = json.loads(result)

        doc = f"{'Received' if data['type'] == 'income' else 'Spent'} ₹{data['amount']} on {data['description']}"

        save_transaction(
            state["user_id"],
            state["collection"],
            data["description"],
            data["amount"],
            data.get("category", "other"),
            data["type"],
            "today",
            doc
        )

        return {**state,
                "transaction_data": data,
                "ai_response": f"✅ Recorded: {doc}\n\nYour {data.get('category', 'other')} spending has been updated!"}
    except:
        return {**state,
                "ai_response": "I couldn't understand that transaction. Can you rephrase?"}

# ─── NODE 3: ADVISOR AGENT ─────────────────────────────
def advisor_node(state: ArthMitraState) -> ArthMitraState:
    question = state["user_message"]
    collection = state["collection"]
    income = state["income"]
    expense = state["expense"]
    categories = state["categories"]

    context = "No transactions yet"
    if collection.count() > 0:
        results = collection.query(
            query_texts=[question],
            n_results=min(5, collection.count())
        )
        context = "\n".join(results['documents'][0])

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
    response = llm.invoke([HumanMessage(content=prompt)])
    return {**state, "ai_response": response.content}

# ─── NODE 4: INVESTMENT AGENT ──────────────────────────
def investment_node(state: ArthMitraState) -> ArthMitraState:
    question = state["user_message"]
    income = state["income"]
    expense = state["expense"]

    balance = income - expense
    monthly_savings = max(0, balance)

    prompt = f"""
You are ArthMitra's Investment Advisor — specialized in Indian personal finance for students.

User's current financial position:
- Total Income: ₹{income:,.0f}
- Total Expenses: ₹{expense:,.0f}  
- Available Balance: ₹{balance:,.0f}
- Estimated monthly savings: ₹{monthly_savings:,.0f}

Investment knowledge base:
- SIP (Systematic Investment Plan): Start from ₹500/month in index funds
- Nifty 50 Index Fund: Low cost, tracks top 50 companies, good for beginners
- PPF (Public Provident Fund): Tax free, 7.1% interest, 15 year lock-in
- ELSS: Tax saving mutual fund, 3 year lock-in, market linked returns
- FD (Fixed Deposit): Safe, 6-7% interest, no market risk
- Emergency Fund Rule: Keep 3-6 months expenses as emergency fund first
- 50-30-20 Rule: 50% needs, 30% wants, 20% savings/investments

User question: {question}

Give specific, actionable advice based on their ACTUAL balance.
If balance is negative or very low — advise to stabilize finances first before investing.
Be friendly, specific, and explain WHY you're recommending something.
Answer in 3-4 lines.
"""
    response = llm.invoke([HumanMessage(content=prompt)])
    return {**state, "ai_response": response.content}

# ─── NODE 5: PREDICTION AGENT ──────────────────────────
def prediction_node(state: ArthMitraState) -> ArthMitraState:
    question = state["user_message"]
    collection = state["collection"]
    income = state["income"]
    expense = state["expense"]
    categories = state["categories"]

    # Get recent transactions for pattern analysis
    context = "No transactions yet"
    if collection.count() > 0:
        results = collection.query(
            query_texts=["spending expenses transactions"],
            n_results=min(8, collection.count())
        )
        context = "\n".join(results['documents'][0])

    balance = income - expense
    cat_summary = "\n".join([f"- {k}: ₹{v:,.0f}" for k, v in categories.items()])

    prompt = f"""
You are ArthMitra's Prediction Engine — you analyze spending patterns and forecast future financial health.

Current financial data:
- Total Income: ₹{income:,.0f}
- Total Expenses: ₹{expense:,.0f}
- Current Balance: ₹{balance:,.0f}
- Spending by category:
{cat_summary}

Recent transactions:
{context}

User question: {question}

Analyze the spending patterns and provide:
1. Current spending velocity — are they spending fast or slow?
2. Prediction — based on current patterns, what will their balance be in 2 weeks? 1 month?
3. Which category is most likely to cause financial stress?
4. One specific actionable recommendation to improve the forecast

Be specific with numbers and dates. Be honest even if the prediction is concerning.
Answer in 4-5 lines.
"""
    response = llm.invoke([HumanMessage(content=prompt)])
    return {**state,
            "ai_response": response.content,
            "predictions": {"analyzed": True}}

# ─── NODE 6: ALERT AGENT ───────────────────────────────
def alert_node(state: ArthMitraState) -> ArthMitraState:
    """Runs on EVERY message — checks for warnings proactively"""
    income = state["income"]
    expense = state["expense"]
    categories = state["categories"]

    balance = income - expense
    alerts = []

    # Check 1 — negative balance
    if balance < 0:
        alerts.append(f"🚨 Your expenses exceed income by ₹{abs(balance):,.0f}!")

    # Check 2 — low balance warning
    elif balance < income * 0.1:
        alerts.append(f"⚠️ Low balance warning — only ₹{balance:,.0f} remaining!")

    # Check 3 — food overspending
    food_spend = categories.get("food", 0)
    if income > 0 and food_spend > income * 0.3:
        alerts.append(f"🍔 Food spending is ₹{food_spend:,.0f} — over 30% of income!")

    # Check 4 — shopping overspending
    shopping_spend = categories.get("shopping", 0)
    if income > 0 and shopping_spend > income * 0.25:
        alerts.append(f"🛍️ Shopping at ₹{shopping_spend:,.0f} — consider cutting back!")

    # Append alerts to response if any
    if alerts:
        current_response = state.get("ai_response", "")
        alert_text = "\n\n**⚡ Financial Alerts:**\n" + "\n".join(alerts)
        return {**state, "ai_response": current_response + alert_text, "alerts": alerts}

    return {**state, "alerts": alerts}

# ─── ROUTING FUNCTION ──────────────────────────────────
def route_after_router(state: ArthMitraState) -> Literal["transaction", "advisor", "investment", "prediction"]:
    intent = state["intent"]
    if intent == "STORE":
        return "transaction"
    elif intent == "INVEST":
        return "investment"
    elif intent == "PREDICT":
        return "prediction"
    else:
        return "advisor"

# ─── BUILD GRAPH ───────────────────────────────────────
def build_graph():
    graph = StateGraph(ArthMitraState)

    # Add all nodes
    graph.add_node("router", router_node)
    graph.add_node("transaction", transaction_node)
    graph.add_node("advisor", advisor_node)
    graph.add_node("investment", investment_node)
    graph.add_node("prediction", prediction_node)
    graph.add_node("alert", alert_node)

    # Entry point
    graph.set_entry_point("router")

    # Router decides which agent handles the message
    graph.add_conditional_edges(
        "router",
        route_after_router,
        {
            "transaction": "transaction",
            "advisor": "advisor",
            "investment": "investment",
            "prediction": "prediction"
        }
    )

    # All agents pass through alert agent before ending
    graph.add_edge("transaction", "alert")
    graph.add_edge("advisor", "alert")
    graph.add_edge("investment", "alert")
    graph.add_edge("prediction", "alert")

    # Alert agent is always last
    graph.add_edge("alert", END)

    return graph.compile()

# ─── COMPILED GRAPH ────────────────────────────────────
arthmitra_graph = build_graph()

# ─── MAIN ENTRY POINT ──────────────────────────────────
def process_message(user_message, user_id, collection, income, expense, categories):
    initial_state = {
        "user_message": user_message,
        "intent": "",
        "user_id": user_id,
        "collection": collection,
        "income": income,
        "expense": expense,
        "categories": categories,
        "transaction_data": {},
        "ai_response": "",
        "alerts": [],
        "predictions": {}
    }

    result = arthmitra_graph.invoke(initial_state)

    agent_map = {
        "STORE": "🔄 Transaction Agent",
        "INVEST": "📈 Investment Agent",
        "PREDICT": "🔮 Prediction Agent",
        "ADVICE": "💡 Advisor Agent",
        "GENERAL": "💡 Advisor Agent"
    }

    agent_used = agent_map.get(result["intent"], "💡 Advisor Agent")

    return result["ai_response"], agent_used, result["alerts"]