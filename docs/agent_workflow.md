# ArthMitra — Agent Workflow

## Overview
ArthMitra uses a LangGraph state machine with 6 nodes (agents).
Every user message flows through this graph.
The fallback system (ai.py) activates if LangGraph fails for any reason.

---

## The 6 Agents

### Agent 1: Router Agent
**Job**: Classifies user message intent
**Input**: raw user message
**Output**: intent string
**Model**: gemini-2.0-flash-lite (fast, cheap)

Intent categories:
- `STORE` — "I spent ₹300 on pizza", "bought earphones for ₹1200"
- `INVEST` — "should I start SIP?", "where to invest ₹5000?"
- `PREDICT` — "will I have enough money next month?", "forecast my spending"
- `ADVICE` — "where does my money go?", "am I overspending?"
- `GENERAL` — anything else → routed to Advisor

---

### Agent 2: Transaction Agent
**Job**: Extracts transaction details and saves to database
**Triggered by**: STORE intent
**Input**: user message
**Output**: confirmation message + saved transaction

Flow:
1. Gemini extracts: description, amount, category, type (expense/income)
2. save_transaction() → Supabase + ChromaDB
3. Returns "✅ Recorded: Spent ₹300 on pizza"

---

### Agent 3: Advisor Agent
**Job**: Answers financial questions using RAG + accurate totals
**Triggered by**: ADVICE or GENERAL intent
**Input**: user question + financial summary + RAG context
**Output**: personalised financial advice

Flow:
1. ChromaDB semantic search → top 5 relevant transactions
2. Supabase get_summary() → accurate totals (income, expense, categories)
3. Both injected into Gemini prompt
4. Returns contextual advice with specific numbers

Key insight: Supabase gives ACCURACY, ChromaDB gives CONTEXT.
Never use RAG alone for totals — always use Supabase for numbers.

---

### Agent 4: Investment Agent
**Job**: Gives investment advice based on actual financial position
**Triggered by**: INVEST intent
**Input**: user question + income/expense/balance
**Output**: personalised investment recommendation

Knowledge base injected into prompt:
- SIP from ₹500/month
- Nifty 50 index funds for beginners
- PPF: tax free, 7.1%, 15 year lock-in
- ELSS: tax saving, 3 year lock-in
- FD: safe, 6-7% interest
- Emergency fund rule: 3-6 months expenses first
- 50-30-20 rule

If balance is negative → advises stabilizing first before investing.

---

### Agent 5: Prediction Agent
**Job**: Forecasts future financial health based on spending patterns
**Triggered by**: PREDICT intent
**Input**: user question + all financial data + upcoming expenses list
**Output**: specific predictions with dates and numbers

Provides:
1. Current spending velocity
2. Balance prediction for 2 weeks and 1 month
3. Impact of upcoming expenses
4. One specific recommendation

Uses upcoming_expenses from Supabase to factor in known future costs.

---

### Agent 6: Alert Agent
**Job**: Proactive financial warnings — runs on EVERY message
**Triggered by**: Always (after any other agent)
**Input**: complete financial state
**Output**: appends alerts to existing response

Alert checks:
1. Over monthly budget → "🚨 Over budget by ₹X!"
2. 90% of budget used → "⚠️ 90% of budget used!"
3. Negative balance → "🚨 Expenses exceed income!"
4. Food > 30% of budget → "🍔 Food spending too high!"
5. Shopping > 25% of budget → "🛍️ Shopping too high!"
6. Low balance + upcoming expense → "📅 Upcoming: X — save now!"

---

## Graph Structure

```python
graph = StateGraph(ArthMitraState)

# Nodes
graph.add_node("router", router_node)
graph.add_node("transaction", transaction_node)
graph.add_node("advisor", advisor_node)
graph.add_node("investment", investment_node)
graph.add_node("prediction", prediction_node)
graph.add_node("alert", alert_node)

# Entry
graph.set_entry_point("router")

# Conditional routing after router
graph.add_conditional_edges("router", route_after_router, {
    "transaction": "transaction",
    "advisor": "advisor",
    "investment": "investment",
    "prediction": "prediction"
})

# All agents → alert → END
graph.add_edge("transaction", "alert")
graph.add_edge("advisor", "alert")
graph.add_edge("investment", "alert")
graph.add_edge("prediction", "alert")
graph.add_edge("alert", END)
```

---

## Fallback System
If LangGraph fails (import error, API error, etc.):
- Falls back to direct ai.py functions
- detect_intent() → extract_transaction() OR get_ai_answer()
- Shows "⚠️ Fallback System" caption in UI
- User experience unaffected

---

## State Object
Everything that flows between agents:
```python
{
    "user_message": str,
    "intent": str,
    "user_id": str,
    "collection": ChromaDB collection object,
    "income": float,
    "expense": float,
    "categories": {"food": 1200.0, ...},
    "transaction_data": {},
    "ai_response": str,
    "alerts": [],
    "predictions": {},
    "monthly_budget": float,
    "upcoming_expense": str   # NOTE: needs update to list from upcoming_expenses table
}
```
