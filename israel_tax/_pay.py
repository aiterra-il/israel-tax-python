from __future__ import annotations

import math
import re
import unicodedata
from typing import Any

from . import _data as data
from ._calc import INVALID_MESSAGE
from ._js import JS_SPACE, js_number, js_round, js_trim

_FULL_PERCENT = 10_000
_MAX_RATE_AGOROT = 1_000_000
_SHEKEL_SUFFIX = re.compile("ש[\"״']?ח$")
_AMOUNT_CHARS = re.compile(r"[0-9.,]+")
_DIGIT = re.compile(r"[0-9]")
_NON_ZERO = re.compile(r"[1-9]")
_PLAIN = re.compile(r"([0-9]*)(?:\.([0-9]*))?")
_WHOLE_MONTHS = re.compile(r"[0-9]+")

SECTOR_PRIVATE = "private"
NOT_ELIGIBLE_MESSAGE = (
    "דמי הבראה מגיעים רק אחרי שמשלימים שנת עבודה ראשונה אצל המעסיק. כשהשנה מסתיימת משלמים 5 ימים בעדה. "
    "מי שעוזב לפני שהשלים שנה לא זכאי לדמי הבראה לפי צו ההרחבה הכללי."
)


def _strip_decoration(value: str) -> str:
    kept = "".join(char for char in value if char not in JS_SPACE and char != "₪" and unicodedata.category(char) != "Cf")
    return _SHEKEL_SUFFIX.sub("", kept, count=1).removesuffix("%")


def _to_plain_decimal(value: str) -> str | None:
    last_dot = value.rfind(".")
    last_comma = value.rfind(",")
    comma_count = value.count(",")
    dot_count = value.count(".")
    if last_dot >= 0 and last_comma >= 0:
        decimal_separator = "." if last_dot > last_comma else ","
        group_separator = "," if decimal_separator == "." else "."
        decimal_count = dot_count if decimal_separator == "." else comma_count
        if decimal_count > 1:
            return None
        return value.replace(group_separator, "").replace(decimal_separator, ".", 1)
    head = value[:last_comma] if last_comma >= 0 else value[:-1]
    grouped_thousands = len(value) - last_comma - 1 == 3 and bool(_NON_ZERO.search(head))
    if comma_count == 1 and not grouped_thousands:
        return value.replace(",", ".", 1)
    if comma_count > 0:
        return value.replace(",", "")
    if dot_count > 1:
        return value.replace(".", "")
    return value


def parse_hundredths(value: str) -> int | None:
    cleaned = _strip_decoration(js_trim(value))
    if not cleaned or not _AMOUNT_CHARS.fullmatch(cleaned) or not _DIGIT.search(cleaned):
        return None
    plain = _to_plain_decimal(cleaned)
    match = _PLAIN.fullmatch(plain) if plain else None
    if not match:
        return None
    whole = re.sub(r"^0+(?=[0-9])", "", match.group(1) or "0")
    if len(whole) > 12:
        return None
    fraction = (match.group(2) or "").ljust(3, "0")
    round_up = 1 if int(fraction[2]) >= 5 else 0
    return int(whole) * 100 + int(fraction[:2]) + round_up


def _amount_invalid(value: str, limit: int) -> bool:
    parsed = parse_hundredths(value)
    if parsed is not None:
        return parsed == 0 or parsed > limit
    return _strip_decoration(js_trim(value)) != ""


def _months_invalid(value: str) -> bool:
    trimmed = js_trim(value)
    if not trimmed:
        return False
    if not _WHOLE_MONTHS.fullmatch(trimmed):
        return True
    return not 1 <= int(trimmed) <= data.MONTHS_IN_YEAR


def _days_for_year(year: float) -> float:
    for row in data.SENIORITY_TABLE:
        if year >= row["from"] and (row["to"] is None or year <= row["to"]):
            return row["days"]
    return 0


def _compute_year(year: float, months: float, percent: int, rate: int) -> tuple[float, float, int]:
    table_days = _days_for_year(year)
    scaled = table_days * percent * months
    divisor = _FULL_PERCENT * data.MONTHS_IN_YEAR
    return table_days, scaled / divisor, js_round((scaled * rate) / divisor)


def recuperation(year_text: str, months_text: str, percent_text: str, rate_text: str) -> dict[str, Any]:
    if _months_invalid(months_text) or _amount_invalid(percent_text, _FULL_PERCENT) or _amount_invalid(rate_text, _MAX_RATE_AGOROT):
        raise ValueError(INVALID_MESSAGE)
    missing = [
        label
        for label, value in (
            ("שנת העבודה", year_text),
            ("חודשי עבודה בשנה", js_trim(months_text)),
            ("היקף המשרה", js_trim(percent_text)),
            ("מחיר יום הבראה", js_trim(rate_text)),
        )
        if not value
    ]
    if missing:
        raise ValueError(f"כדי לראות את התוצאה, מלאו: {', '.join(missing)}.")
    year = js_number(year_text)
    months = js_number(months_text)
    if year == 1 and months < data.MONTHS_IN_YEAR:
        raise ValueError(NOT_ELIGIBLE_MESSAGE)
    percent_parsed = parse_hundredths(percent_text)
    rate_parsed = parse_hundredths(rate_text)
    percent = _FULL_PERCENT if percent_parsed is None else percent_parsed
    rate = data.DAY_RATE_AGOROT if rate_parsed is None else rate_parsed
    table_days, days, amount = _compute_year(year, months, percent, rate)
    top_up = (
        _compute_year(year, months, percent, data.DAY_RATE_AGOROT - data.PREVIOUS_RATE_AGOROT)[2]
        if rate == data.DAY_RATE_AGOROT
        else None
    )
    return {
        "kind": "result",
        "year": _plain(year),
        "table_days": table_days,
        "months": _plain(months),
        "percent": percent,
        "rate": rate,
        "days": days,
        "amount": amount,
        "top_up": top_up,
    }


def _plain(value: float) -> float:
    return int(value) if math.isfinite(value) and value.is_integer() else value


def _period_by_id(period: str) -> dict[str, Any]:
    return next((item for item in data.WAGE_PERIODS if item["id"] == period), data.WAGE_PERIODS[0])


def _group_by_id(age: str) -> dict[str, Any]:
    return next((item for item in data.AGE_GROUPS if item["id"] == age), data.AGE_GROUPS[0])


def full_monthly(period: str, age: str) -> int:
    adult = _period_by_id(period)["adult"]["monthly"]
    return math.floor((adult * _group_by_id(age)["percent"]) / 100)


def hourly_rate(period: str, age: str) -> int:
    if age != "adult":
        return math.floor(full_monthly(period, age) / data.YOUTH_HOURS_DIVISOR)
    return _period_by_id(period)["adult"]["hourly182"]


def daily_rate(period: str, week: str) -> int:
    adult = _period_by_id(period)["adult"]
    return adult["daily5"] if week == "5" else adult["daily6"]
