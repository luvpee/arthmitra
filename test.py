import chromadb
from google import genai
import time
import json

import os
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("GOOGLE_API_KEY")
client = genai.Client(api_key=API_KEY)

chroma_client = chromadb.PersistentClient(path="./arthmitra_memory")
collection = chroma_client.get_or_create_collection(name="arthmitra_v2")

# Sample starting transactions
starting_transactions = [
    ("Swiggy food delivery", 350, "food"),
    ("Dominos pizza", 280, "food"),
    ("Bus fare", 200, "transport"),
    ("College canteen", 150, "food"),
    ("Stationery", 100, "education"),
    ("Amazon earphones", 1200, "shopping"),
]

for i, (desc, amount, category) in enumerate(starting_transactions):
    try:
        collection.add(
            documents=[f"Spent ₹{amount} on {desc}"],
            metadatas=[{"amount": amount, "category": category, "type": "expense"}],
            ids=[f"start_txn_{i}"]
        )
    except:
        pass

# Models with fallback
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
                print("⏳ Switching model...")
                time.sleep(3)
                continue
            else:
                return None
    return None

def detect_intent(message):
    prompt = f"""
Analyze this message and respond with ONLY one word.
Message: "{message}"
If the user is recording a transaction (spending or receiving money), respond: STORE
If the user is asking a question or seeking advice, respond: ANSWER
Only respond with STORE or ANSWER. Nothing else.
"""
    result = call_gemini(prompt)
    if result:
        return result.strip().upper()
    return "ANSWER"

def extract_transaction(message):
    prompt = f"""
Extract transaction details from this message and respond ONLY with valid JSON.
Message: "{message}"
Respond with exactly this format:
{{"description": "what was bought/received", "amount": 000, "category": "food/transport/education/shopping/income/other", "type": "expense or income"}}
No extra text. Just the JSON.
"""
    result = call_gemini(prompt)
    if result:
        try:
            result = result.replace("```json", "").replace("```", "").strip()
            return json.loads(result)
        except:
            return None
    return None

def store_transaction(data, collection):
    import uuid
    txn_id = f"txn_{uuid.uuid4().hex[:8]}"
    doc = f"{'Received' if data['type'] == 'income' else 'Spent'} ₹{data['amount']} on {data['description']}"
    collection.add(
        documents=[doc],
        metadatas=[{
            "amount": data["amount"],
            "category": data["category"],
            "type": data["type"]
        }],
        ids=[txn_id]
    )
    return doc

def answer_question(question, collection):
    results = collection.query(
        query_texts=[question],
        n_results=min(6, collection.count())
    )
    context = "\n".join(results['documents'][0])

    prompt = f"""
You are ArthMitra, personal AI CA for Indian students.
User's recent transactions:
{context}

Monthly budget: ₹5000
College fees due in 3 weeks: ₹15000

Question: {question}
Reply in 2-3 lines. Be specific with numbers. Be friendly and direct.
"""
    return call_gemini(prompt)

# Main chat loop
print("🤖 ArthMitra ready! Talk naturally — tell me what you spent or ask anything.")
print("Examples: 'I spent ₹200 on groceries' or 'how much have I spent?'")
print("Type 'quit' to exit.\n")

while True:
    user_input = input("You: ").strip()

    if user_input.lower() == 'quit':
        print("ArthMitra: Stay financially smart! 💰")
        break

    if not user_input:
        continue

    # Step 1 — detect intent
    intent = detect_intent(user_input)

    if intent == "STORE":
        # Step 2a — extract and store transaction
        data = extract_transaction(user_input)
        if data:
            doc = store_transaction(data, collection)
            print(f"ArthMitra: ✅ Got it! I've recorded — {doc}\n")
        else:
            print("ArthMitra: I couldn't understand that transaction. Can you rephrase?\n")
    else:
        # Step 2b — answer the question
        answer = answer_question(user_input, collection)
        if answer:
            print(f"ArthMitra: {answer}\n")
        else:
            print("ArthMitra: Having trouble connecting. Try again!\n")