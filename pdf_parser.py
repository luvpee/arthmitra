import fitz
from ai import call_gemini
import json
import os

def parse_pdf(uploaded_file):
    with open("temp.pdf", "wb") as f:
        f.write(uploaded_file.read())
    doc = fitz.open("temp.pdf")
    text = "".join(page.get_text() for page in doc)
    doc.close()
    # Clean up temp file
    os.remove("temp.pdf")

    prompt = f"""
Extract all transactions from this bank statement.
Return ONLY a JSON array:
[{{"date": "DD-Mon-YY", "description": "...", "amount": 000, "type": "expense or income"}}]
Amount always positive. Type exactly "expense" or "income".
Text: {text}
"""
    result = call_gemini(prompt)
    if result:
        try:
            result = result.replace("```json", "").replace("```", "").strip()
            return json.loads(result)
        except:
            return None
    return None