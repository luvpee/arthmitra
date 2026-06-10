import time
import json
from google import genai
import os
from dotenv import load_dotenv

load_dotenv()
gemini_client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))
MODELS = ["gemini-2.5-flash", "gemini-2.0-flash", "gemini-2.0-flash-lite"]

def call_gemini(prompt):
    for model in MODELS:
        try:
            response = gemini_client.models.generate_content(
                model=model, contents=prompt)
            return response.text
        except Exception as e:
            if "503" in str(e) or "429" in str(e):
                time.sleep(3)
                continue
            return None
    return None

def detect_intent(message):
    result = call_gemini(f"""
Respond with ONE word only.
Message: "{message}"
If recording a transaction (spending/receiving money): STORE
If asking a question or advice: ANSWER
""")
    return result.strip().upper() if result else "ANSWER"

def extract_transaction(message):
    result = call_gemini(f"""
Extract transaction from this message. Return ONLY valid JSON:
{{"description": "...", "amount": 000, "category": "food/transport/education/shopping/entertainment/health/other", "type": "expense or income"}}
Message: "{message}"
""")
    if result:
        try:
            result = result.replace("```json", "").replace("```", "").strip()
            return json.loads(result)
        except:
            return None
    return None

def get_ai_answer(question, collection, income, expense, categories):
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
    return call_gemini(prompt)