from fpdf import FPDF

pdf = FPDF()
pdf.add_page()
pdf.set_font("Helvetica", "B", 16)
pdf.cell(0, 10, "STATE BANK OF INDIA", ln=True, align="C")
pdf.set_font("Helvetica", size=10)
pdf.cell(0, 8, "Account Statement - June 2024", ln=True, align="C")
pdf.cell(0, 8, "Account Holder: Aryan Kumar | A/C: XXXX1234", ln=True, align="C")
pdf.ln(5)

# Table header
pdf.set_font("Helvetica", "B", 10)
pdf.set_fill_color(200, 200, 200)
pdf.cell(35, 8, "Date", border=1, fill=True)
pdf.cell(85, 8, "Description", border=1, fill=True)
pdf.cell(35, 8, "Amount", border=1, fill=True)
pdf.cell(35, 8, "Balance", border=1, fill=True)
pdf.ln()

# Transactions
pdf.set_font("Helvetica", size=9)
transactions = [
    ("01-Jun-24", "Opening Balance", "", "5000.00"),
    ("02-Jun-24", "UPI/Swiggy Order/Food", "-350.00", "4650.00"),
    ("03-Jun-24", "UPI/Dominos Pizza", "-280.00", "4370.00"),
    ("04-Jun-24", "ATM Withdrawal", "-500.00", "3870.00"),
    ("05-Jun-24", "UPI/College Canteen", "-150.00", "3720.00"),
    ("06-Jun-24", "NEFT/Pocket Money/DAD", "+2000.00", "5720.00"),
    ("08-Jun-24", "UPI/Amazon Purchase", "-1200.00", "4520.00"),
    ("10-Jun-24", "UPI/Bus Pass Recharge", "-200.00", "4320.00"),
    ("12-Jun-24", "UPI/Zomato Order", "-220.00", "4100.00"),
    ("14-Jun-24", "UPI/Stationery Shop", "-100.00", "4000.00"),
    ("15-Jun-24", "UPI/Netflix Subscription", "-149.00", "3851.00"),
    ("18-Jun-24", "UPI/Paytm/Mobile Recharge", "-99.00", "3752.00"),
    ("20-Jun-24", "UPI/Gym Membership", "-500.00", "3252.00"),
    ("22-Jun-24", "NEFT/Freelance Payment", "+1500.00", "4752.00"),
    ("25-Jun-24", "UPI/Swiggy Order/Food", "-180.00", "4572.00"),
    ("28-Jun-24", "UPI/Book Purchase", "-250.00", "4322.00"),
    ("30-Jun-24", "UPI/College Fest Entry", "-100.00", "4222.00"),
]

for date, desc, amount, balance in transactions:
    pdf.cell(35, 7, date, border=1)
    pdf.cell(85, 7, desc, border=1)
    pdf.cell(35, 7, amount, border=1)
    pdf.cell(35, 7, balance, border=1)
    pdf.ln()

pdf.ln(10)
pdf.set_font("Helvetica", "B", 10)
pdf.cell(0, 8, "Total Debits: -4278.00  |  Total Credits: +3500.00", ln=True)

pdf.output("sample_statement.pdf")
print("✅ Sample bank statement created: sample_statement.pdf")