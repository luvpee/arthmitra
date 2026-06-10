import fitz  # pymupdf
from google import genai
import chromadb
import json
import os
import uuid
import time
from dotenv import load_dotenv

load_dotenv()

client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))
chroma_client = chromadb.PersistentClient(path="./arthmitra_memory")
collection = chroma_client.get_or_create_collection(name="arthmitra_pdf")

MODELS = ["gemini-2.5-flash", "gemini-2.0-flash", "gemini-2.0-flash-lite"]

def call_gemini(prompt):
    for model in MODELS:
        try:
            response = client.models.generate_content(
                model=model,
                contents=prompt
            )
            return response.text
        except Exception as e:
            if "503" in str(e) or "429" in str(e):
                print(f"⏳ Switching model...")
                time.sleep(3)
                continue
            else:
                return None
    return None

def extract_text_from_pdf(pdf_path):
    doc = fitz.open(pdf_path)
    text = ""
    for page in doc:
        text += page.get_text()
    doc.close()
    return text

def extract_transactions_with_ai(raw_text):
    prompt = f"""
You are a bank statement parser. Extract all transactions from this bank statement text.
For each transaction return a JSON array with this exact format:
[
  {{"date": "DD-Mon-YY", "description": "transaction description", "amount": 000, "type": "expense or income"}},
  ...
]

Rules:
- Negative amounts or debits = expense
- Positive amounts or credits = income
- Amount should always be positive number
- type should be exactly "expense" or "income"
- Return ONLY the JSON array, no other text

Bank statement text:
{raw_text}
"""
    result = call_gemini(prompt)
    if result:
        try:
            result = result.replace("```json", "").replace("```", "").strip()
            return json.loads(result)
        except:
            return None
    return None

def categorize_transaction(description):
    food_keywords = ["swiggy", "zomato", "dominos", "canteen", "food", "restaurant", "cafe"]
    transport_keywords = ["bus", "uber", "ola", "metro", "auto", "petrol"]
    education_keywords = ["college", "book", "stationery", "library", "course"]
    shopping_keywords = ["amazon", "flipkart", "myntra", "mall", "shop"]
    entertainment_keywords = ["netflix", "spotify", "movie", "fest", "game"]
    health_keywords = ["gym", "medical", "pharmacy", "doctor", "hospital"]

    desc_lower = description.lower()

    if any(k in desc_lower for k in food_keywords):
        return "food"
    elif any(k in desc_lower for k in transport_keywords):
        return "transport"
    elif any(k in desc_lower for k in education_keywords):
        return "education"
    elif any(k in desc_lower for k in shopping_keywords):
        return "shopping"
    elif any(k in desc_lower for k in entertainment_keywords):
        return "entertainment"
    elif any(k in desc_lower for k in health_keywords):
        return "health"
    else:
        return "other"

def store_transactions(transactions):
    stored = 0
    for txn in transactions:
        try:
            category = categorize_transaction(txn["description"])
            doc = f"{'Received' if txn['type'] == 'income' else 'Spent'} ₹{txn['amount']} on {txn['description']} on {txn['date']}"

            collection.add(
                documents=[doc],
                metadatas=[{
                    "amount": float(txn["amount"]),
                    "category": category,
                    "type": txn["type"],
                    "date": txn["date"]
                }],
                ids=[f"pdf_txn_{uuid.uuid4().hex[:8]}"]
            )
            stored += 1
        except Exception as e:
            pass
    return stored

# Main
print("📄 ArthMitra PDF Parser")
print("=" * 40)

pdf_path = "sample_statement.pdf"
print(f"📖 Reading {pdf_path}...")
raw_text = extract_text_from_pdf(pdf_path)
print(f"✅ Extracted {len(raw_text)} characters from PDF")
print("\n📊 Raw text preview:")
print(raw_text[:300])
print("...")

print("\n🤖 Sending to Gemini for transaction extraction...")
transactions = extract_transactions_with_ai(raw_text)

if transactions:
    print(f"\n✅ Found {len(transactions)} transactions!")
    print("\n📋 Extracted transactions:")
    for txn in transactions:
        emoji = "💰" if txn["type"] == "income" else "💸"
        print(f"{emoji} {txn['date']} | {txn['description']} | ₹{txn['amount']} | {txn['type']}")

    print("\n💾 Storing in ArthMitra memory...")
    stored = store_transactions(transactions)
    print(f"✅ {stored} transactions stored in ChromaDB!")
else:
    print("❌ Could not extract transactions. Try again.")