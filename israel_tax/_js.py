from __future__ import annotations

import math
import re
from collections.abc import Iterable
from decimal import Decimal

JS_SPACE = (
    "\t\n\v\f\r   "
    + "".join(chr(code) for code in range(0x2000, 0x200B))
    + "    　﻿"
)

_DECIMAL = re.compile(r"[+-]?(?:[0-9]+\.?[0-9]*|\.[0-9]+)(?:[eE][+-]?[0-9]+)?")
_RADIX = {"0x": 16, "0o": 8, "0b": 2}


def js_round(value: float) -> int:
    floor = math.floor(value)
    return floor + 1 if value - floor >= 0.5 else floor


def js_trim(value: str) -> str:
    return value.strip(JS_SPACE)


def js_str(value: float | int | str) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value)
    if math.isnan(value):
        return "NaN"
    if math.isinf(value):
        return "Infinity" if value > 0 else "-Infinity"
    if value == 0:
        return "0"
    if value.is_integer() and abs(value) < 1e21:
        return str(int(value))
    text = repr(value)
    if "e" in text and 1e-7 <= abs(value) < 1e21:
        return format(Decimal(text), "f")
    return text


def js_number(value: object) -> float:
    if isinstance(value, bool):
        return 1.0 if value else 0.0
    if isinstance(value, (int, float)):
        return float(value)
    if value is None:
        return 0.0
    text = js_trim(str(value))
    if not text:
        return 0.0
    if _DECIMAL.fullmatch(text):
        return float(text)
    if text in ("Infinity", "+Infinity"):
        return math.inf
    if text == "-Infinity":
        return -math.inf
    radix = _RADIX.get(text[:2].lower())
    if radix:
        try:
            return float(int(text[2:], radix))
        except ValueError:
            return math.nan
    return math.nan


def total(values: Iterable[float]) -> float:
    result: float = 0
    for value in values:
        result += value
    return result
