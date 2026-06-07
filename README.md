# 💰 ArthMitra - Personal AI Chartered Accountant

An AI-powered personal finance advisor for Indian students built using RAG architecture.

## Features
- Natural language expense tracking
- Persistent financial memory using ChromaDB
- Personalised advice based on actual transaction history
- Intent detection — understands if you're logging or asking
- Multi-model fallback for reliability

## Tech Stack
- Google Gemini API
- LangChain + ChromaDB (RAG Pipeline)
- Streamlit (Web UI)
- Python

## How to Run
1. Clone the repo
2. Create `.env` file with `GOOGLE_API_KEY=your_key`
3. Install dependencies: `pip install -r requirements.txt`
4. Run: `streamlit run app.py`