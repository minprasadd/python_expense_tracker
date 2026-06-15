"""
CLI Expense Tracker with JSON storage.
Usage: python expense_tracker.py [command] [arguments]
"""

import json
import os
import sys
from datetime import datetime
from collections import defaultdict

DATA_FILE = "expenses.json"

CATEGORIES = ["food",'gym', "transport", "shopping", "health", "entertainment", "education", "other"]
CATEGORY_ICONS = {
    "food":          "🍔",
    "gym":           "💪",
    "transport":     "🚌",
    "shopping":      "🛍️",
    "health":        "💊",
    "entertainment": "🎬",
    "education":     "📚",
    "other":         "📦",
}


def load_data():
    if not os.path.exists(DATA_FILE):
        return {"expenses": [], "budget": None}
    with open(DATA_FILE, "r") as f:
        return json.load(f)


def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)


def next_id(expenses):
    return max((e["id"] for e in expenses), default=0) + 1


def current_month():
    return datetime.now().strftime("%Y-%m")


def parse_month(expenses, month=None):
    """Filter expenses by month string 'YYYY-MM'. Defaults to current month."""
    m = month or current_month()
    return [e for e in expenses if e["date"].startswith(m)], m


def add_expense(args):
    """
    Add an expense.
    Usage: python expense_tracker.py add <amount> <category> [description]
    """
    if len(args) < 2:
        print("⚠️  Usage: python expense_tracker.py add <amount> <category> [description]")
        print(f"   Categories: {', '.join(CATEGORIES)}")
        return

    # Validate amount
    try:
        amount = float(args[0])
        if amount <= 0:
            raise ValueError
    except ValueError:
        print("⚠️  Amount must be a positive number. E.g.: 250.50")
        return

    # Validate category
    category = args[1].lower()
    if category not in CATEGORIES:
        print(f"⚠️  Invalid category '{category}'. Choose from: {', '.join(CATEGORIES)}")
        return

    description = " ".join(args[2:]) if len(args) > 2 else ""

    data = load_data()
    expense = {
        "id":          next_id(data["expenses"]),
        "amount":      amount,
        "category":    category,
        "description": description,
        "date":        datetime.now().strftime("%Y-%m-%d %H:%M"),
    }
    data["expenses"].append(expense)

    # Budget warning
    monthly, m = parse_month(data["expenses"])
    total = sum(e["amount"] for e in monthly)
    save_data(data)

    icon = CATEGORY_ICONS.get(category, "📦")
    print(f"✅ Added expense [{expense['id']}]: {icon} {category.capitalize()} — ₹{amount:.2f}"
          + (f"  ({description})" if description else ""))

    if data["budget"]:
        pct = (total / data["budget"]) * 100
        if total > data["budget"]:
            print(f"🚨 Budget exceeded! Spent ₹{total:.2f} of ₹{data['budget']:.2f} this month.")
        elif pct >= 80:
            print(f"⚠️  Warning: You've used {pct:.0f}% of your monthly budget (₹{total:.2f}/₹{data['budget']:.2f}).")


def list_expenses(args):
    """
    List expenses.
    Usage: python expense_tracker.py list [--month YYYY-MM] [--category <cat>]
    """
    data = load_data()
    month = None
    category_filter = None

    # Parse optional flags
    i = 0
    while i < len(args):
        if args[i] == "--month" and i + 1 < len(args):
            month = args[i + 1]
            i += 2
        elif args[i] == "--category" and i + 1 < len(args):
            category_filter = args[i + 1].lower()
            i += 2
        else:
            i += 1

    expenses, m = parse_month(data["expenses"], month)

    if category_filter:
        expenses = [e for e in expenses if e["category"] == category_filter]

    if not expenses:
        print(f"📭 No expenses found for {m}" + (f" in category '{category_filter}'" if category_filter else "") + ".")
        return

    label = f"Expenses — {m}" + (f" | {category_filter.capitalize()}" if category_filter else "")
    print(f"\n{'─'*58}")
    print(f"  {label}")
    print(f"{'─'*58}")
    for e in expenses:
        icon = CATEGORY_ICONS.get(e["category"], "📦")
        desc = f"  \033[2m{e['description']}\033[0m" if e["description"] else ""
        print(f"  [{e['id']:>3}]  {icon} {e['category'].capitalize():<14} ₹{e['amount']:>8.2f}{desc}"
              f"  \033[2m{e['date']}\033[0m")
    print(f"{'─'*58}")
    total = sum(e["amount"] for e in expenses)
    print(f"  {'Total':>20}          ₹{total:>8.2f}")
    print(f"{'─'*58}\n")


def summary(args):
    """
    Show spending summary grouped by category.
    Usage: python expense_tracker.py summary [--month YYYY-MM]
    """
    data = load_data()
    month = None
    if "--month" in args:
        idx = args.index("--month")
        if idx + 1 < len(args):
            month = args[idx + 1]

    expenses, m = parse_month(data["expenses"], month)

    if not expenses:
        print(f"📭 No expenses for {m}.")
        return

    totals = defaultdict(float)
    for e in expenses:
        totals[e["category"]] += e["amount"]

    grand_total = sum(totals.values())
    budget = data.get("budget")

    print(f"\n{'─'*45}")
    print(f"  📊 Summary — {m}")
    print(f"{'─'*45}")
    for cat, amt in sorted(totals.items(), key=lambda x: -x[1]):
        icon = CATEGORY_ICONS.get(cat, "📦")
        pct = (amt / grand_total) * 100
        bar = "█" * int(pct / 5)
        print(f"  {icon} {cat.capitalize():<14} ₹{amt:>8.2f}  {bar} {pct:.0f}%")
    print(f"{'─'*45}")
    print(f"  {'Total':<20} ₹{grand_total:>8.2f}")

    if budget:
        remaining = budget - grand_total
        pct_used = (grand_total / budget) * 100
        status = "🚨 OVER BUDGET" if remaining < 0 else "✅ Within budget"
        print(f"  {'Budget':<20} ₹{budget:>8.2f}")
        print(f"  {'Remaining':<20} ₹{remaining:>8.2f}  {status}")
        print(f"  Budget used: {pct_used:.1f}%")
    print(f"{'─'*45}\n")


def set_budget(args):
    """
    Set a monthly budget.
    Usage: python expense_tracker.py budget <amount>
    """
    if not args:
        print("⚠️  Usage: python expense_tracker.py budget <amount>  E.g.: budget 5000")
        return
    try:
        amount = float(args[0])
        if amount <= 0:
            raise ValueError
    except ValueError:
        print("⚠️  Budget must be a positive number.")
        return

    data = load_data()
    data["budget"] = amount
    save_data(data)
    print(f"🎯 Monthly budget set to ₹{amount:.2f}")


def delete_expense(args):
    """
    Delete an expense by ID.
    Usage: python expense_tracker.py delete <id>
    """
    if not args or not args[0].isdigit():
        print("⚠️  Usage: python expense_tracker.py delete <id>")
        return
    expense_id = int(args[0])
    data = load_data()
    new_expenses = [e for e in data["expenses"] if e["id"] != expense_id]
    if len(new_expenses) == len(data["expenses"]):
        print(f"❌ No expense found with ID {expense_id}.")
    else:
        data["expenses"] = new_expenses
        save_data(data)
        print(f"🗑️  Deleted expense [{expense_id}].")


HELP = """
💰 CLI Expense Tracker
──────────────────────────────────────────────────
Usage: python expense_tracker.py <command> [args]

Commands:
  add <amount> <category> [description]
                      Add a new expense
                      Categories: food, transport, shopping,
                                  health, entertainment, education, other

  list                List this month's expenses
  list --month YYYY-MM         List a specific month
  list --category <cat>        Filter by category

  summary             Show this month's summary by category
  summary --month YYYY-MM      Show a specific month's summary

  budget <amount>     Set your monthly budget
  delete <id>         Delete an expense by ID
  help                Show this help message

Examples:
  python expense_tracker.py add 250 food Lunch at cafe
  python expense_tracker.py add 1200 transport Monthly bus pass
  python expense_tracker.py list
  python expense_tracker.py list --month 2026-05
  python expense_tracker.py summary
  python expense_tracker.py budget 10000
  python expense_tracker.py delete 3
──────────────────────────────────────────────────
"""


def main():
    args = sys.argv[1:]

    if not args or args[0] in ("help", "--help", "-h"):
        print(HELP)

    elif args[0] == "add":
        add_expense(args[1:])

    elif args[0] == "list":
        list_expenses(args[1:])

    elif args[0] == "summary":
        summary(args[1:])

    elif args[0] == "budget":
        set_budget(args[1:])

    elif args[0] == "delete":
        delete_expense(args[1:])

    else:
        print(f"❓ Unknown command: '{args[0]}'. Run 'python expense_tracker.py help' for usage.")


if __name__ == "__main__":
    main()
