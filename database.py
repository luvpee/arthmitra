import chromadb
import uuid
import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()
supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

def load_chromadb(user_id):
    chroma = chromadb.Client()
    col = chroma.get_or_create_collection(f"arthmitra_{user_id[:8]}")
    try:
        rows = supabase.table("transactions").select("*").eq("user_id", user_id).execute().data
        for row in rows:
            try:
                col.add(
                    documents=[row["document"]],
                    metadatas=[{"amount": row["amount"],
                                "category": row["category"],
                                "type": row["type"],
                                "date": row["date"]}],
                    ids=[row["id"]]
                )
            except:
                pass
    except:
        pass
    return col

def get_summary(user_id):
    try:
        rows = supabase.table("transactions").select("*").eq("user_id", user_id).execute().data
        income, expense, cats = 0, 0, {}
        for r in rows:
            if r["type"] == "income":
                income += r["amount"]
            else:
                expense += r["amount"]
                cats[r["category"]] = cats.get(r["category"], 0) + r["amount"]
        return income, expense, cats
    except:
        return 0, 0, {}

def save_transaction(user_id, collection, description, amount, category, txn_type, date, document):
    txn_id = str(uuid.uuid4())
    supabase.table("transactions").insert({
        "id": txn_id,
        "user_id": user_id,
        "description": description,
        "amount": float(amount),
        "category": category,
        "type": txn_type,
        "date": date,
        "document": document
    }).execute()
    try:
        collection.add(
            documents=[document],
            metadatas=[{"amount": float(amount), "category": category,
                        "type": txn_type, "date": date}],
            ids=[txn_id]
        )
    except:
        pass
    return txn_id

def get_user_profile(user_id):
    try:
        result = supabase.table("user_profiles").select("*").eq("user_id", user_id).execute()
        if result.data:
            return result.data[0]
        return {"monthly_budget": 5000}
    except:
        return {"monthly_budget": 5000}

def save_user_profile(user_id, monthly_budget):
    try:
        existing = supabase.table("user_profiles").select("*").eq("user_id", user_id).execute()
        if existing.data:
            supabase.table("user_profiles").update({
                "monthly_budget": monthly_budget,
                "updated_at": "now()"
            }).eq("user_id", user_id).execute()
        else:
            supabase.table("user_profiles").insert({
                "user_id": user_id,
                "monthly_budget": monthly_budget
            }).execute()
    except:
        pass