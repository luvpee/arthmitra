def categorize(description):
    desc = description.lower()
    if any(k in desc for k in ["swiggy", "zomato", "dominos", "canteen", "food", "restaurant"]):
        return "food"
    elif any(k in desc for k in ["bus", "uber", "ola", "metro", "auto", "fuel"]):
        return "transport"
    elif any(k in desc for k in ["college", "book", "stationery", "library", "course"]):
        return "education"
    elif any(k in desc for k in ["amazon", "flipkart", "myntra", "shopping", "mall"]):
        return "shopping"
    elif any(k in desc for k in ["netflix", "spotify", "movie", "fest", "game"]):
        return "entertainment"
    elif any(k in desc for k in ["gym", "medical", "pharmacy", "doctor", "hospital"]):
        return "health"
    elif any(k in desc for k in ["salary", "pocket money", "neft", "freelance", "deposit"]):
        return "income"
    else:
        return "other"