from datetime import datetime, timezone


ARABIC_MONTHS = {
    1: "يناير",
    2: "فبراير",
    3: "مارس",
    4: "أبريل",
    5: "مايو",
    6: "يونيو",
    7: "يوليو",
    8: "أغسطس",
    9: "سبتمبر",
    10: "أكتوبر",
    11: "نوفمبر",
    12: "ديسمبر",
}


def format_arabic_date(unix_timestamp: int) -> str:
    dt = datetime.fromtimestamp(unix_timestamp, tz=timezone.utc)
    return f"{dt.day} {ARABIC_MONTHS[dt.month]}"


def format_price(price_str: str) -> str:
    price = float(price_str)
    return "مجاناً" if price == 0.0 else f"{price}$"
