# ArthMitra — Database Schema (Updated)

## Supabase Project

URL format:

`https://xxxxxx.supabase.co`

All tables are inside the `public` schema.

Currently:

* RLS (Row Level Security) is DISABLED
* User isolation is manually handled using `user_id` filtering in queries

---

# Table 1: transactions

Core table storing all income and expense transactions.

```sql
CREATE TABLE transactions (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,

    user_id TEXT NOT NULL,              -- Supabase auth UUID

    description TEXT NOT NULL,          -- e.g. "Swiggy order"
    amount FLOAT NOT NULL,              -- Always stored as positive number

    category TEXT,                      -- food/transport/etc.
    type TEXT,                          -- "income" or "expense"

    date TEXT,                          -- Flexible text date format
    document TEXT,                      -- Semantic searchable text for ChromaDB

    created_at TIMESTAMP DEFAULT NOW()
);
```

---

## Purpose

This is the primary financial table of the application.

Every user transaction is stored here and later:

* used for analytics
* used for dashboard summaries
* embedded into ChromaDB for AI querying
* used for category-wise insights

---

## Important Notes

### amount

Always stored as a positive float.

Example:

```python
350.0
```

Transaction direction is determined using:

```python
type = "income" or "expense"
```

---

### document

Stores AI-friendly semantic text.

Example:

```text
Spent ₹350 on Swiggy food delivery on 02-Jun-24
```

Used for:

* vector embeddings
* semantic retrieval
* chatbot memory/context

---

## Key Queries Used

### Get all transactions for a user

```python
supabase.table("transactions") \
    .select("*") \
    .eq("user_id", user_id) \
    .execute()
```

---

### Insert new transaction

```python
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
```

---

# Table 2: user_profiles

Stores persistent user preferences and profile information.

One row per user.

```sql
CREATE TABLE user_profiles (
    user_id TEXT PRIMARY KEY,

    monthly_budget FLOAT DEFAULT 5000,

    full_name TEXT DEFAULT 'Mitra',

    updated_at TIMESTAMP DEFAULT NOW()
);
```

---

## Purpose

Used for:

* monthly budget tracking
* dashboard personalization
* greeting users by name
* future personalization features

---

## Important Notes

### full_name

Added later using migration:

```sql
ALTER TABLE public.user_profiles
ADD COLUMN full_name text DEFAULT 'Mitra';
```

Fallback value in backend:

```python
"Mitra"
```

---

## Key Queries Used

### Get profile

```python
supabase.table("user_profiles") \
    .select("*") \
    .eq("user_id", user_id) \
    .execute()
```

---

### Update existing profile

```python
supabase.table("user_profiles").update({
    "monthly_budget": monthly_budget,
    "full_name": full_name,
    "updated_at": "now()"
}).eq("user_id", user_id).execute()
```

---

### Create new profile

```python
supabase.table("user_profiles").insert({
    "user_id": user_id,
    "monthly_budget": monthly_budget,
    "full_name": full_name
}).execute()
```

---

# Table 3: upcoming_expenses

Stores future financial commitments/reminders.

Multiple rows allowed per user.

```sql
CREATE TABLE upcoming_expenses (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,

    user_id TEXT NOT NULL,

    description TEXT NOT NULL,
    amount FLOAT NOT NULL,

    due_date TEXT NOT NULL,

    created_at TIMESTAMP DEFAULT NOW()
);
```

---

## Purpose

Used for:

* future expense planning
* reminders
* budget forecasting
* financial awareness

---

## Key Queries Used

### Get upcoming expenses

```python
supabase.table("upcoming_expenses") \
    .select("*") \
    .eq("user_id", user_id) \
    .order("due_date") \
    .execute()
```

---

### Add upcoming expense

```python
supabase.table("upcoming_expenses").insert({
    "id": str(uuid.uuid4()),
    "user_id": user_id,
    "description": description,
    "amount": float(amount),
    "due_date": str(due_date)
}).execute()
```

---

### Delete upcoming expense

```python
supabase.table("upcoming_expenses") \
    .delete() \
    .eq("id", expense_id) \
    .execute()
```

---

# ChromaDB Integration

ArthMitra uses ChromaDB as an in-memory vector database for semantic financial search.

Collections are rebuilt from Supabase on every app startup.

---

## Collection Naming

```python
arthmitra_{first_8_chars_of_user_id}
```

Example:

```python
arthmitra_a81f29bc
```

---

# ChromaDB Document Structure

Each transaction is converted into a vector document.

```python
collection.add(
    documents=[
        "Spent ₹350 on Swiggy food delivery on 02-Jun-24"
    ],

    metadatas=[{
        "amount": 350.0,
        "category": "food",
        "type": "expense",
        "date": "02-Jun-24"
    }],

    ids=["same-uuid-as-transaction"]
)
```

---

# ChromaDB Loading Logic

Executed during app startup.

```python
rows = supabase.table("transactions") \
    .select("*") \
    .eq("user_id", user_id) \
    .execute().data
```

Each row is inserted into the vector collection.

---

# Semantic Query Pattern

```python
results = collection.query(
    query_texts=["user question"],
    n_results=min(5, collection.count())
)

context = "\n".join(results['documents'][0])
```

---

# Current Categories Used

## Expense Categories

* `food`

  * Swiggy
  * Zomato
  * restaurant
  * canteen

* `transport`

  * Uber
  * Ola
  * bus
  * fuel
  * metro

* `education`

  * college fees
  * books
  * stationery

* `shopping`

  * Amazon
  * Flipkart
  * Myntra
  * mall purchases

* `entertainment`

  * Netflix
  * Spotify
  * movies
  * fest expenses

* `health`

  * gym
  * pharmacy
  * doctor
  * medicines

* `income`

  * salary
  * freelance
  * pocket money
  * bank transfer

* `other`

  * uncategorized transactions

---

# Backend Utility Functions

Current database layer contains these helper functions:

```python
load_chromadb(user_id)
get_summary(user_id)
save_transaction(...)
get_user_profile(user_id)
save_user_profile(...)
get_upcoming_expenses(user_id)
add_upcoming_expense(...)
delete_upcoming_expense(...)
```

---

# Architecture Flow

```text
User Action
    ↓
Streamlit Frontend
    ↓
Database Layer (database.py)
    ↓
Supabase Storage
    ↓
ChromaDB Semantic Memory
    ↓
LLM Context Retrieval
```

---

# Current Limitations

* RLS disabled
* Dates stored as TEXT instead of DATE
* ChromaDB rebuilt every startup
* No indexing yet
* No transaction editing support
* No soft delete system
* No recurring expenses support

---

# Planned Future Improvements

* Enable Supabase RLS
* Use proper DATE columns
* Add transaction editing
* Add recurring subscriptions tracking
* Add investment tracking
* Add AI-generated spending insights
* Persistent ChromaDB storage
* Add category analytics tables
* Add OCR bill parsing pipeline

```
```
