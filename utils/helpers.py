from datetime import datetime


def format_currency(amount, currency="Rs."):
    return f"{currency}{amount:,.2f}"


def timestamp_now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def print_banner(text):
    line = "=" * 50
    print(f"\n{line}")
    print(f"  {text}")
    print(f"{line}\n")
