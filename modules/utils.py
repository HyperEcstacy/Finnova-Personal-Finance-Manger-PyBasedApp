from datetime import datetime

def get_current_timestamp():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def calculate_totals(data):
    total_income = sum(item["amount"] for item in data["income"])
    total_expenses = sum(item["amount"] for item in data["expenses"])
    return {"income": total_income, "expenses": total_expenses, "balance": total_income - total_expenses}
