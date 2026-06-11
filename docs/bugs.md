# ArthMitra — Known Bugs & Issues

---

## 🐛 Active Bugs

### Bug 1: upcoming_expense is string not list
**File**: agents.py
**Severity**: Medium
**Description**: ArthMitraState has `upcoming_expense: str` but it should be a list of dicts from the upcoming_expenses Supabase table.
**Current behavior**: Only one upcoming expense can be passed to Prediction Agent
**Fix needed**: 
1. Change state type to `upcoming_expenses: list`
2. Update process_message() to accept list
3. Update prediction_node() prompt to format list properly
4. Update app.py to fetch and pass list

---

### Bug 2: Chat history lost on page refresh
**File**: app.py
**Severity**: Low
**Description**: st.session_state.messages resets when user refreshes browser
**Current behavior**: Chat disappears after refresh, financial data stays (Supabase)
**Fix needed**: Store messages in Supabase messages table, load on login
**Workaround**: Financial data is preserved, only chat text is lost

---

### Bug 3: Duplicate transactions on PDF re-upload
**File**: pdf_parser.py, app.py
**Severity**: Medium
**Description**: If user uploads same PDF twice, all transactions are stored twice
**Current behavior**: Supabase gets duplicate rows, totals become incorrect
**Fix needed**: Check for existing transactions before inserting (by description + amount + date + user_id)
**Workaround**: User should clear transactions before re-uploading same PDF

---

### Bug 4: Monthly budget not persisted
**File**: app.py
**Severity**: Medium  
**Description**: Monthly budget input in sidebar uses session state, resets on refresh
**Current behavior**: Budget defaults to ₹5000 every time user opens app
**Fix needed**: 
1. Load from user_profiles table on login
2. Save to user_profiles table on "Save Profile" button click
**Note**: database.py already has get_user_profile() and save_user_profile() ready

---

### Bug 5: Profile loaded flag not cleared on logout
**File**: app.py
**Severity**: Low
**Description**: If user logs out and logs in as different user, old profile might persist in session
**Fix needed**: Clear profile_loaded from session state in sign_out() function in auth.py

---

## ✅ Fixed Bugs

### Fixed: ChromaDB data mixing between test runs
**Fixed by**: Clearing all test data from Supabase and using user_id filtering

### Fixed: API key exposed in git history
**Fixed by**: Deleted repo, recreated clean with .gitignore

### Fixed: Wrong expense totals from RAG
**Fixed by**: Using Supabase directly for totals, RAG only for context

### Fixed: Protobuf version conflict on Streamlit Cloud
**Fixed by**: Pinning chromadb==0.4.24, protobuf==3.20.3, numpy==1.26.4

### Fixed: NumPy 2.0 incompatibility with ChromaDB 0.4.24
**Fixed by**: Pinning numpy==1.26.4

### Fixed: LangChain import error (langchain.schema)
**Fixed by**: Changed to `from langchain_core.messages import HumanMessage`

---

## ⚠️ Known Limitations

### Rate Limiting
- Gemini free tier has daily limits
- LangGraph makes 2 API calls per message (router + agent)
- Heavy testing can exhaust quota
- **Workaround**: Multiple API keys from different Google accounts

### ChromaDB Memory
- ChromaDB is in-memory only on deployment
- Rebuilds from Supabase on every app start
- First message after startup may be slower (ChromaDB loading)

### Streamlit Session
- Each browser tab is a separate session
- Opening ArthMitra in two tabs simultaneously may cause issues

### PDF Parsing Accuracy
- Works best on digital/typed PDFs
- Scanned PDFs may have lower accuracy
- Very complex table layouts may miss some transactions
