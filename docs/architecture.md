# ArthMitra — System Architecture

## Tech Stack
- **Frontend/UI**: Streamlit (Python)
- **LLM**: Google Gemini API (gemini-2.5-flash, gemini-2.0-flash, gemini-2.0-flash-lite)
- **Agent Framework**: LangGraph + LangChain
- **Vector Database**: ChromaDB (in-memory, rebuilt from Supabase on startup)
- **Persistent Database**: Supabase (PostgreSQL)
- **PDF Parsing**: PyMuPDF (fitz)
- **Authentication**: Supabase Auth
- **Deployment**: Streamlit Cloud (auto-deploys on GitHub push)
- **Embeddings**: all-MiniLM-L6-v2 (via ChromaDB default)

## System Flow

```
User opens arthmitra.streamlit.app
            ↓
    Supabase Auth (Login/Signup)
            ↓
    Load user transactions from Supabase → ChromaDB
    Load user profile (budget, etc.) from Supabase
            ↓
    User interacts via chat or PDF upload
            ↓
    LangGraph Multi-Agent System processes message
            ↓
    Response + Alerts returned to UI
```

## Two Database Architecture
ArthMitra uses TWO databases working together:

**Supabase (Permanent)**
- Source of truth for all data
- Stores transactions, user profiles, upcoming expenses
- Queried directly for accurate financial totals
- Data never lost even if server restarts

**ChromaDB (Fast Search)**
- In-memory vector database
- Rebuilt from Supabase every time app starts
- Used for semantic similarity search
- Answers questions like "which expenses seem impulsive?"

## Why Two Databases?
- SQL (Supabase) is perfect for: totals, sums, filtering by user
- Vector DB (ChromaDB) is perfect for: semantic queries, pattern finding
- Using both gives accuracy + intelligence

## File Structure
```
arthmitra/
├── app.py              # Main Streamlit UI + entry point
├── agents.py           # LangGraph multi-agent system
├── auth.py             # Supabase authentication
├── database.py         # All Supabase operations
├── ai.py               # Direct Gemini calls (fallback system)
├── pdf_parser.py       # PDF text extraction + AI parsing
├── utils.py            # Transaction categorization
└── requirements.txt    # Dependencies
```

## Model Fallback Strategy
```python
MODELS = ["gemini-2.5-flash", "gemini-2.0-flash", "gemini-2.0-flash-lite"]
```
If primary model hits quota/503 → automatically tries next model.
LangGraph also has fallback to direct ai.py if LangGraph itself fails.

## Data Flow for PDF Upload
```
PDF file uploaded
    ↓
PyMuPDF extracts raw text
    ↓
Gemini parses text → JSON array of transactions
    ↓
Keyword categorization (food/transport/education etc.)
    ↓
Save to Supabase (permanent) + ChromaDB (semantic search)
    ↓
Sidebar updates with new totals
```

## Data Flow for Chat Message
```
User types message
    ↓
LangGraph Router Agent classifies intent
    ↓
Appropriate agent handles it:
  STORE → Transaction Agent → Supabase + ChromaDB
  ADVICE → Advisor Agent → ChromaDB RAG + Supabase totals
  INVEST → Investment Agent → Supabase totals + knowledge base
  PREDICT → Prediction Agent → ChromaDB patterns + upcoming expenses
  GENERAL → Advisor Agent
    ↓
Alert Agent runs on EVERY message → checks budget/balance
    ↓
Response + alerts returned to user
```
