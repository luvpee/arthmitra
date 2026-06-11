# ArthMitra — API Contracts

All function signatures across all files.

---

## database.py

```python
def load_chromadb(user_id: str) -> chromadb.Collection
# Loads user transactions from Supabase into in-memory ChromaDB
# Returns: ChromaDB collection with all user transactions as embeddings

def get_summary(user_id: str) -> tuple[float, float, dict]
# Returns: (total_income, total_expense, categories_dict)
# categories_dict = {"food": 1200.0, "shopping": 500.0, ...}
# Always queries Supabase directly for accuracy

def save_transaction(
    user_id: str,
    collection: chromadb.Collection,
    description: str,
    amount: float,
    category: str,
    txn_type: str,          # "expense" or "income"
    date: str,
    document: str           # Full text for ChromaDB
) -> str                    # Returns transaction UUID

def get_user_profile(user_id: str) -> dict
# Returns: {"monthly_budget": 5000.0}
# Returns default if profile doesn't exist

def save_user_profile(user_id: str, monthly_budget: float) -> None

def get_upcoming_expenses(user_id: str) -> list[dict]
# Returns: [{"id": "uuid", "description": "College fees", "amount": 15000.0, "due_date": "Jun 25"}, ...]

def add_upcoming_expense(user_id: str, description: str, amount: float, due_date: str) -> bool

def delete_upcoming_expense(expense_id: str) -> bool
```

---

## ai.py (Fallback System)

```python
def call_gemini(prompt: str) -> str | None
# Tries models in order: gemini-2.5-flash → gemini-2.0-flash → gemini-2.0-flash-lite
# Returns: response text or None if all fail

def detect_intent(message: str) -> str
# Returns: "STORE" or "ANSWER"

def extract_transaction(message: str) -> dict | None
# Returns: {"description": str, "amount": float, "category": str, "type": str}
# Returns None if parsing fails

def get_ai_answer(
    question: str,
    collection: chromadb.Collection,
    income: float,
    expense: float,
    categories: dict
) -> str | None
# Combines RAG context + Supabase totals for accurate answers
```

---

## agents.py (LangGraph System)

```python
def process_message(
    user_message: str,
    user_id: str,
    collection: chromadb.Collection,
    income: float,
    expense: float,
    categories: dict,
    monthly_budget: float = 5000,
    upcoming_expense: str = ""
) -> tuple[str, str, list]
# Returns: (response_text, agent_used_label, alerts_list)
# agent_used_label example: "🔄 Transaction Agent"
# alerts_list example: ["🚨 Over budget by ₹500!"]
```

**ArthMitraState TypedDict:**
```python
class ArthMitraState(TypedDict):
    user_message: str
    intent: str                 # STORE/INVEST/PREDICT/ADVICE/GENERAL
    user_id: str
    collection: object
    income: float
    expense: float
    categories: dict
    transaction_data: dict
    ai_response: str
    alerts: list
    predictions: dict
    monthly_budget: float
    upcoming_expense: str
```

---

## auth.py

```python
def sign_up(email: str, password: str) -> tuple[User | None, str | None]
# Returns: (user_object, error_message)

def sign_in(email: str, password: str) -> tuple[User | None, str | None]
# Returns: (user_object, error_message)

def sign_out() -> None
# Clears session state and reruns app

def show_login_page() -> None
# Renders full login/signup UI
```

---

## pdf_parser.py

```python
def parse_pdf(uploaded_file: UploadedFile) -> list[dict] | None
# Takes Streamlit uploaded file object
# Extracts text with PyMuPDF
# Sends to Gemini for parsing
# Returns: [{"date": str, "description": str, "amount": float, "type": str}, ...]
# Returns None if parsing fails
```

---

## utils.py

```python
def categorize(description: str) -> str
# Keyword-based categorization
# Returns one of: food/transport/education/shopping/entertainment/health/income/other
```

---

## LangGraph Nodes

```python
def router_node(state) -> state          # Sets state["intent"]
def transaction_node(state) -> state     # Saves transaction, sets state["ai_response"]
def advisor_node(state) -> state         # RAG + summary answer, sets state["ai_response"]
def investment_node(state) -> state      # Investment advice, sets state["ai_response"]
def prediction_node(state) -> state      # Spending forecast, sets state["ai_response"]
def alert_node(state) -> state           # Appends alerts to state["ai_response"]
```

**Graph edges:**
```
router → (conditional) → transaction | advisor | investment | prediction
transaction → alert → END
advisor → alert → END
investment → alert → END
prediction → alert → END
```
