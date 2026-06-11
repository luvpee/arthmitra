# ArthMitra — Database Schema

## Supabase Project
URL format: https://xxxxxx.supabase.co
All tables are in the public schema.
RLS (Row Level Security) is currently DISABLED for simplicity.
User isolation is handled manually via user_id filtering in queries.

---

## Table 1: transactions

The core table. Stores every financial transaction for every user.

```sql
CREATE TABLE transactions (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id TEXT NOT NULL,              -- Supabase auth user UUID
    description TEXT NOT NULL,          -- e.g. "Swiggy food delivery"
    amount FLOAT NOT NULL,              -- Always positive number
    category TEXT,                      -- food/transport/education/shopping/entertainment/health/income/other
    type TEXT,                          -- "expense" or "income"
    date TEXT,                          -- "DD-Mon-YY" format or "today"
    document TEXT,                      -- Full text stored in ChromaDB e.g. "Spent ₹350 on Swiggy food delivery"
    created_at TIMESTAMP DEFAULT NOW()
);
```

**Key queries used:**
```python
# Get all transactions for a user
supabase.table("transactions").select("*").eq("user_id", user_id).execute()

# Insert new transaction
supabase.table("transactions").insert({...}).execute()
```

---

## Table 2: user_profiles

Stores user preferences. One row per user.

```sql
CREATE TABLE user_profiles (
    user_id TEXT PRIMARY KEY,           -- Supabase auth user UUID
    monthly_budget FLOAT DEFAULT 5000,  -- User's self-defined monthly budget in ₹
    updated_at TIMESTAMP DEFAULT NOW()
);
```

**Key queries used:**
```python
# Get profile
supabase.table("user_profiles").select("*").eq("user_id", user_id).execute()

# Upsert profile
supabase.table("user_profiles").update({...}).eq("user_id", user_id).execute()
supabase.table("user_profiles").insert({...}).execute()
```

---

## Table 3: upcoming_expenses

Stores list of upcoming financial commitments. Multiple rows per user.

```sql
CREATE TABLE upcoming_expenses (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id TEXT NOT NULL,              -- Supabase auth user UUID
    description TEXT NOT NULL,          -- e.g. "College fees"
    amount FLOAT NOT NULL,              -- Amount in ₹
    due_date TEXT NOT NULL,             -- e.g. "Jun 25, 2026"
    created_at TIMESTAMP DEFAULT NOW()
);
```

**Key queries used:**
```python
# Get all upcoming expenses for a user
supabase.table("upcoming_expenses").select("*").eq("user_id", user_id).execute()

# Add upcoming expense
supabase.table("upcoming_expenses").insert({...}).execute()

# Delete upcoming expense
supabase.table("upcoming_expenses").delete().eq("id", expense_id).execute()
```

---

## ChromaDB Collections

ChromaDB is in-memory and rebuilt from Supabase on every app start.

**Collection name**: `arthmitra_{first_8_chars_of_user_id}`

Each document stored:
```python
collection.add(
    documents=["Spent ₹350 on Swiggy food delivery on 02-Jun-24"],
    metadatas=[{
        "amount": 350.0,
        "category": "food",
        "type": "expense",
        "date": "02-Jun-24"
    }],
    ids=["uuid-string"]  # Same UUID as Supabase transaction id
)
```

**Query pattern:**
```python
results = collection.query(
    query_texts=["user question here"],
    n_results=min(5, collection.count())
)
context = "\n".join(results['documents'][0])
```

---

## Category Values
Valid categories used throughout the system:
- `food` — Swiggy, Zomato, Dominos, canteen, restaurant
- `transport` — bus, Uber, Ola, metro, fuel
- `education` — college, books, stationery, library
- `shopping` — Amazon, Flipkart, Myntra, mall
- `entertainment` — Netflix, Spotify, movie, fest
- `health` — gym, medical, pharmacy, doctor
- `income` — salary, pocket money, NEFT, freelance
- `other` — everything else
