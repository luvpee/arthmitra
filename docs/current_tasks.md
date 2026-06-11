# ArthMitra — Current Tasks

## Status: Active Development
Last updated: June 11, 2026

---

## ✅ COMPLETED

### Core System
- [x] Gemini API connection working
- [x] ChromaDB RAG pipeline working
- [x] Supabase persistent storage
- [x] PDF bank statement upload + parsing
- [x] Natural language transaction recording
- [x] Intent detection (STORE vs ANSWER)
- [x] Accurate financial summaries from Supabase
- [x] Multi-model fallback (gemini-2.5-flash → 2.0-flash → 2.0-flash-lite)

### Multi-Agent System (LangGraph)
- [x] Router Agent (5 intent categories)
- [x] Transaction Agent
- [x] Advisor Agent (RAG + Supabase totals)
- [x] Investment Agent (Indian finance knowledge base)
- [x] Prediction Agent (spending forecasts)
- [x] Alert Agent (runs on every message)
- [x] Fallback to ai.py if LangGraph fails

### UI
- [x] Streamlit web UI
- [x] Login/Signup pages (Supabase Auth)
- [x] Sidebar with financial summary
- [x] Budget progress bar
- [x] Spending breakdown by category
- [x] PDF upload section
- [x] Chat interface

### Infrastructure
- [x] Modular file structure (app.py, agents.py, auth.py, database.py, ai.py, pdf_parser.py, utils.py)
- [x] Deployed on Streamlit Cloud: arthmitra.streamlit.app
- [x] GitHub: github.com/luvpee/arthmitra
- [x] .gitignore (API keys protected)
- [x] User data isolation (each user sees only their own data)

### Database
- [x] transactions table (with user_id column)
- [x] user_profiles table (monthly_budget)
- [x] upcoming_expenses table (description, amount, due_date)

---

## 🔄 IN PROGRESS

### User Profile System
- [ ] Connect monthly_budget input to Supabase user_profiles table
  - database.py has get_user_profile() and save_user_profile() ready
  - Need to add to app.py: load profile on login, save on button click
  - Need to add "💾 Save Profile" button in sidebar

### Upcoming Expenses Feature
- [ ] Add upcoming expenses UI to sidebar
  - Form: description + amount + due_date + Add button
  - List: show all upcoming with delete button
  - database.py has get_upcoming_expenses(), add_upcoming_expense(), delete_upcoming_expense() ready
  - Need sidebar UI in app.py

- [ ] Pass upcoming expenses LIST to Prediction Agent
  - Currently passing single string upcoming_expense
  - Should pass full list from Supabase
  - Update agents.py process_message() signature
  - Update prediction_node() to use list

---

## 📋 TODO (Next Steps)

### High Priority
- [ ] Fix upcoming_expense in state — change from string to list
- [ ] Add upcoming expenses sidebar UI
- [ ] Load/save user profile from Supabase on login
- [ ] Push all changes to GitHub
- [ ] Redeploy on Streamlit Cloud

### Medium Priority
- [ ] Remove debug agent caption from UI (st.caption showing agent name)
  - Keep for development, remove before final demo
- [ ] Add chat history persistence to Supabase
  - Currently chat resets on page refresh
  - Store messages in Supabase messages table
- [ ] Add "Clear all transactions" button for user
- [ ] Handle duplicate PDF uploads (same transactions uploaded twice)

### Nice to Have
- [ ] Data export — download transactions as CSV
- [ ] Monthly report generation
- [ ] WhatsApp/SMS integration for transaction auto-detection
- [ ] Dark mode

---

## 🐛 Known Issues
See bugs.md for details.

---

## 📁 Files to Update Next Session

1. **app.py** — Add upcoming expenses UI + load user profile on login
2. **agents.py** — Update upcoming_expense from string to list in state + prediction_node
3. **database.py** — Already has all functions ready, no changes needed

## How to Continue in New Chat
1. Share this file + architecture.md + api_contracts.md
2. Say: "Continue building ArthMitra. Read these context files."
3. Start with current_tasks.md IN PROGRESS section
