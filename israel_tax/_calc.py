from __future__ import annotations

import math
import re
from collections.abc import Mapping, Sequence
from datetime import date
from typing import Any

from . import _data as data
from ._js import js_round, js_trim, total

FULL = 10_000
_EPOCH = date(1970, 1, 1).toordinal()

Bracket = Mapping[str, Any]


def apply_rate(amount: float, basis_points: float) -> int:
    return js_round((amount * basis_points) / FULL)


def _scale_annual(annual: float, months: float) -> float:
    return (annual * months) / data.MONTHS_IN_YEAR


def _split_btl(income: float, rates: Mapping[str, Mapping[str, int]]) -> dict[str, Any]:
    base = min(max(0, income), data.BTL_MAX_INCOME_MONTHLY)
    reduced_part = min(base, data.BTL_REDUCED_LIMIT_MONTHLY)
    full_part = base - reduced_part
    national = apply_rate(reduced_part, rates["national"]["reduced"]) + apply_rate(full_part, rates["national"]["full"])
    health = apply_rate(reduced_part, rates["health"]["reduced"]) + apply_rate(full_part, rates["health"]["full"])
    return {
        "base": base,
        "reduced_part": reduced_part,
        "full_part": full_part,
        "national": national,
        "health": health,
        "total": national + health,
    }


def income_tax(taxable: float, credit_points_hundredths: float, months: float) -> dict[str, Any]:
    lower: float = 0
    rows = []
    for bracket in data.ANNUAL_TAX_BRACKETS:
        upper = None if bracket["up_to"] is None else _scale_annual(bracket["up_to"], months)
        income = max(0, min(taxable, math.inf if upper is None else upper) - lower)
        rows.append(
            {
                "from": 0 if lower == 0 else lower + 1,
                "to": upper,
                "rate_basis_points": bracket["rate_basis_points"],
                "income": income,
                "tax": apply_rate(income, bracket["rate_basis_points"]),
            }
        )
        lower = lower if upper is None else upper
    surtax_threshold = _scale_annual(data.ANNUAL_SURTAX_THRESHOLD, months)
    surtax_income = max(0, taxable - surtax_threshold)
    surtax = apply_rate(surtax_income, data.SURTAX_RATE_BASIS_POINTS)
    gross = total(row["tax"] for row in rows) + surtax
    credit_value = js_round((credit_points_hundredths * _scale_annual(data.CREDIT_POINT_ANNUAL, months)) / 100)
    credit_used = min(gross, credit_value)
    return {
        "taxable": taxable,
        "rows": rows,
        "surtax_threshold": surtax_threshold,
        "surtax_income": surtax_income,
        "surtax": surtax,
        "gross": gross,
        "credit_points_hundredths": credit_points_hundredths,
        "credit_value": credit_value,
        "credit_used": credit_used,
        "net": gross - credit_used,
    }


def _pension_credit(gross: float) -> int:
    eligible_salary = min(gross, data.PENSION_CREDIT_SALARY_CEILING_MONTHLY)
    eligible_deposit = min(
        (gross * data.PENSION_EMPLOYEE_BASIS_POINTS) / FULL,
        (eligible_salary * data.PENSION_CREDIT_SHARE_BASIS_POINTS) / FULL,
    )
    return apply_rate(eligible_deposit, data.PENSION_CREDIT_RATE_BASIS_POINTS)


def salary(gross: int, credit_points_hundredths: float, hishtalmut: bool, severance: str) -> dict[str, Any]:
    hishtalmut_benefit = (
        apply_rate(max(0, gross - data.HISHTALMUT_SALARY_CEILING_MONTHLY), data.HISHTALMUT_EMPLOYER_BASIS_POINTS)
        if hishtalmut
        else 0
    )
    taxable = gross + hishtalmut_benefit
    tax_on_income = income_tax(taxable, credit_points_hundredths, 1)
    pension_credit = min(tax_on_income["net"], _pension_credit(gross))
    tax = tax_on_income["net"] - pension_credit
    btl = _split_btl(taxable, data.BTL_EMPLOYEE_RATES)
    pension = apply_rate(gross, data.PENSION_EMPLOYEE_BASIS_POINTS)
    employee_hishtalmut = apply_rate(gross, data.HISHTALMUT_EMPLOYEE_BASIS_POINTS) if hishtalmut else 0
    deductions = tax + btl["total"] + pension + employee_hishtalmut
    employer_btl = _split_btl(
        taxable,
        {"national": data.BTL_EMPLOYER_RATES, "health": {"reduced": 0, "full": 0}},
    )["national"]
    employer_pension = apply_rate(gross, data.PENSION_EMPLOYER_BASIS_POINTS)
    severance_basis_points = data.SEVERANCE_BASIS_POINTS[severance]
    employer_severance = apply_rate(gross, severance_basis_points)
    employer_hishtalmut = apply_rate(gross, data.HISHTALMUT_EMPLOYER_BASIS_POINTS) if hishtalmut else 0
    employer_total = employer_btl + employer_pension + employer_severance + employer_hishtalmut
    return {
        "gross": gross,
        "hishtalmut_benefit": hishtalmut_benefit,
        "taxable": taxable,
        "income_tax": tax_on_income,
        "pension_credit": pension_credit,
        "tax": tax,
        "btl": btl,
        "pension": pension,
        "hishtalmut": employee_hishtalmut,
        "deductions": deductions,
        "net": gross - deductions,
        "employer": {
            "btl": employer_btl,
            "pension": employer_pension,
            "severance": employer_severance,
            "severance_basis_points": severance_basis_points,
            "hishtalmut": employer_hishtalmut,
            "total": employer_total,
            "cost": gross + employer_total,
        },
    }


def gross_for_net(target_net: int, credit_points_hundredths: float, hishtalmut: bool, severance: str) -> int | None:
    if target_net <= 0:
        return 0
    low = 0
    high = data.MAX_GROSS_MONTHLY
    if salary(high, credit_points_hundredths, hishtalmut, severance)["net"] < target_net:
        return None
    while high - low > 1:
        middle = (low + high) // 2
        if salary(middle, credit_points_hundredths, hishtalmut, severance)["net"] >= target_net:
            high = middle
        else:
            low = middle
    return high


def vat_breakdown(agorot: int, mode: str, basis_points: int) -> dict[str, int]:
    if mode == "add":
        vat = js_round((agorot * basis_points) / FULL)
        return {"net": agorot, "vat": vat, "gross": agorot + vat}
    net = js_round((agorot * FULL) / (FULL + basis_points))
    return {"net": net, "vat": agorot - net, "gross": agorot}


def _apply_brackets(value: float, brackets: Sequence[Bracket]) -> tuple[list[dict[str, Any]], float]:
    lower: float = 0
    rows = []
    for bracket in brackets:
        upper = bracket["up_to"]
        amount = max(0, min(value, math.inf if upper is None else upper) - lower)
        rows.append(
            {
                "from": 0 if lower == 0 else lower + 1,
                "to": upper,
                "rate_basis_points": bracket["rate_basis_points"],
                "amount": amount,
                "tax": apply_rate(amount, bracket["rate_basis_points"]),
            }
        )
        lower = lower if upper is None else upper
    return rows, total(row["tax"] for row in rows)


def _brackets_for(kind: str) -> Sequence[Bracket]:
    if kind == "additional":
        return data.ADDITIONAL_BRACKETS
    if kind == "oleh":
        return data.OLEH_BRACKETS
    return data.SINGLE_BRACKETS


def purchase_tax(value_agorot: int, kind: str) -> dict[str, Any]:
    value = js_round(value_agorot / 100)
    oleh_benefit_denied = kind == "oleh" and value > data.OLEH_VALUE_CEILING
    rows, tax = _apply_brackets(value, _brackets_for("single" if oleh_benefit_denied else kind))
    single_tax = _apply_brackets(value, data.SINGLE_BRACKETS)[1] if kind == "oleh" else tax
    return {
        "kind": kind,
        "value": value,
        "rows": rows,
        "tax": tax,
        "effective_rate": tax / value if value > 0 else 0,
        "oleh_benefit_denied": oleh_benefit_denied,
        "saving_versus_single": max(0, single_tax - tax),
    }


def _btl_base(profit: float, reduced_limit: float) -> float:
    share = data.BTL_DEDUCTIBLE_BASIS_POINTS / FULL
    t1 = data.BTL_SELF_EMPLOYED_RATES["national"]["reduced"] / FULL
    t2 = data.BTL_SELF_EMPLOYED_RATES["national"]["full"] / FULL
    below_limit = profit / (1 + share * t1)
    if below_limit <= reduced_limit:
        return below_limit
    return (profit + share * reduced_limit * (t2 - t1)) / (1 + share * t2)


def self_employed_btl(profit: float, months: float) -> dict[str, Any]:
    reduced_limit = data.BTL_REDUCED_LIMIT_MONTHLY * months
    ceiling = data.BTL_MAX_INCOME_MONTHLY * months
    minimum = data.BTL_MIN_INCOME_MONTHLY * months
    if profit <= 0:
        return {
            "base": 0,
            "reduced_limit": reduced_limit,
            "reduced_part": 0,
            "full_part": 0,
            "national_reduced": 0,
            "national_full": 0,
            "health_reduced": 0,
            "health_full": 0,
            "national": 0,
            "health": 0,
            "total": 0,
            "deductible": 0,
            "minimum_applied": False,
            "ceiling_applied": False,
        }
    raw = js_round(_btl_base(profit, reduced_limit))
    base = min(max(raw, minimum), ceiling)
    reduced_part = min(base, reduced_limit)
    full_part = base - reduced_part
    rates = data.BTL_SELF_EMPLOYED_RATES
    national_reduced = apply_rate(reduced_part, rates["national"]["reduced"])
    national_full = apply_rate(full_part, rates["national"]["full"])
    health_reduced = apply_rate(reduced_part, rates["health"]["reduced"])
    health_full = apply_rate(full_part, rates["health"]["full"])
    national = national_reduced + national_full
    health = health_reduced + health_full
    return {
        "base": base,
        "reduced_limit": reduced_limit,
        "reduced_part": reduced_part,
        "full_part": full_part,
        "national_reduced": national_reduced,
        "national_full": national_full,
        "health_reduced": health_reduced,
        "health_full": health_full,
        "national": national,
        "health": health,
        "total": national + health,
        "deductible": min(profit, apply_rate(national, data.BTL_DEDUCTIBLE_BASIS_POINTS)),
        "minimum_applied": raw < minimum,
        "ceiling_applied": raw > ceiling,
    }


def _marginal_rate(taxable: float, months: float) -> int:
    if taxable <= 0:
        return 0
    bracket = next(
        (item for item in data.ANNUAL_TAX_BRACKETS if item["up_to"] is None or taxable <= _scale_annual(item["up_to"], months)),
        None,
    )
    surtax = data.SURTAX_RATE_BASIS_POINTS if taxable > _scale_annual(data.ANNUAL_SURTAX_THRESHOLD, months) else 0
    return (bracket["rate_basis_points"] if bracket else 0) + surtax


def self_employed(revenue_agorot: int, expenses_agorot: int, credit_points_hundredths: float, months: float) -> dict[str, Any]:
    revenue = js_round(revenue_agorot / 100)
    expenses = js_round(expenses_agorot / 100)
    difference = revenue - expenses
    profit = max(0, difference)
    btl = self_employed_btl(profit, months)
    tax_on_income = income_tax(profit - btl["deductible"], credit_points_hundredths, months)
    combined = tax_on_income["net"] + btl["total"]
    return {
        "months": months,
        "revenue": revenue,
        "expenses": expenses,
        "profit": profit,
        "loss": difference < 0,
        "btl": btl,
        "income_tax": tax_on_income,
        "total": combined,
        "net": profit - combined,
        "effective_rate": combined / profit if profit > 0 else 0,
        "marginal_rate_basis_points": _marginal_rate(tax_on_income["taxable"], months),
        "advance_rate": tax_on_income["net"] / revenue if revenue > 0 else 0,
    }


_ISO = re.compile(r"([0-9]{4})-([0-9]{2})-([0-9]{2})")
_MONEY = re.compile(r"[0-9]+(?:\.[0-9]{1,2})?")
_MONEY_NOISE = re.compile("[," + re.escape("\t\n\v\f\r       　﻿") + " - ₪]")
_MIN_YEAR = 1950
_MAX_YEAR = 2099
_DAYS_IN_MONTH_FOR_FRACTION = 30

INVALID_MESSAGE = "כדי לראות את התוצאה, תקנו את השדה שמתחתיו הודעת שגיאה."
SEVERANCE_INCOMPLETE = "כדי לראות את התוצאה, מלאו תאריך תחילת עבודה, תאריך סיום ושכר חודשי אחרון."


def _day_of(year: int, month: int, day: int) -> int:
    return date(year, month, 1).toordinal() + day - 1 - _EPOCH


def _date_of(day: int) -> date:
    return date.fromordinal(day + _EPOCH)


def _parse_iso(value: str) -> int | None:
    trimmed = js_trim(value)
    match = _ISO.fullmatch(trimmed)
    if not match:
        return None
    year, month, day = (int(part) for part in match.groups())
    if year < _MIN_YEAR or year > _MAX_YEAR:
        return None
    try:
        parsed = date(year, month, day)
    except ValueError:
        return None
    return parsed.toordinal() - _EPOCH


def _parse_money(value: str) -> float | None:
    cleaned = _MONEY_NOISE.sub("", value)
    if not _MONEY.fullmatch(cleaned):
        return None
    parsed = float(cleaned)
    return parsed if 0 < parsed <= data.MAX_SALARY else None


def _tenure(start_day: int, end_day: int) -> dict[str, float]:
    exclusive_end = end_day + 1
    start = _date_of(start_day)
    end = _date_of(exclusive_end)
    months = (end.year - start.year) * 12 + (end.month - start.month)
    if end.day < start.day:
        months -= 1
    anchor_month = start.month - 1 + months
    anchor = _day_of(start.year + anchor_month // 12, anchor_month % 12 + 1, start.day)
    extra_days = max(0, exclusive_end - anchor)
    fraction = min(extra_days, _DAYS_IN_MONTH_FOR_FRACTION) / _DAYS_IN_MONTH_FOR_FRACTION
    return {"months": months, "extra_days": extra_days, "years": (months + fraction) / 12}


def severance(start_text: str, end_text: str, salary_text: str, section14: str) -> dict[str, Any]:
    start = _parse_iso(start_text) if js_trim(start_text) else None
    end = _parse_iso(end_text) if js_trim(end_text) else None
    has_error = (
        (bool(js_trim(start_text)) and start is None)
        or (bool(js_trim(end_text)) and end is None)
        or (start is not None and end is not None and end < start)
        or (bool(js_trim(salary_text)) and _parse_money(salary_text) is None)
    )
    if has_error:
        raise ValueError(INVALID_MESSAGE)
    monthly = _parse_money(salary_text)
    if start is None or end is None or monthly is None:
        raise ValueError(SEVERANCE_INCOMPLETE)
    tenure = _tenure(start, end)
    eligible = tenure["months"] >= data.MIN_SENIORITY_YEARS * 12
    amount = js_round(monthly * tenure["years"] * 100) / 100 if eligible else 0
    end_year = _date_of(end).year
    exempt = (
        min(amount, js_round(data.EXEMPTION_CEILING_PER_YEAR * tenure["years"] * 100) / 100)
        if end_year == data.EXEMPTION_CEILING_YEAR and eligible
        else None
    )
    return {
        "kind": "result",
        "tenure": tenure,
        "salary": monthly,
        "eligible_by_seniority": eligible,
        "section14": section14,
        "severance": amount,
        "exempt": exempt,
        "taxable": None if exempt is None else js_round((amount - exempt) * 100) / 100,
        "end_year": end_year,
        "start_day": start,
        "end_day": end,
    }


def _month_index(month: int, year: int) -> int:
    return year * 12 + (month - 1)


def _oleh_twelfths(month: int, year: int) -> int:
    result = 0
    for current in range(1, 13):
        position = _month_index(current, data.TAX_YEAR) - _month_index(month, year)
        if position < 0:
            continue
        for stage in data.OLEH_SCHEDULE:
            if position < stage["months"]:
                result += stage["twelfths"]
                break
            position -= stage["months"]
    return result


def _soldier_twelfths(month: int, year: int, full_service: bool) -> int:
    per_month = data.SOLDIER_TWELFTHS_FULL if full_service else data.SOLDIER_TWELFTHS_SHORT
    result = 0
    for current in range(1, 13):
        position = _month_index(current, data.TAX_YEAR) - _month_index(month, year)
        if 1 <= position <= data.SOLDIER_MONTHS:
            result += per_month
    return result


DEGREE_LABELS = {"first": "תואר ראשון", "second": "תואר שני"}


def credits(
    gender: str,
    children: Mapping[str, float],
    degree: str,
    oleh: Mapping[str, int] | None,
    soldier: Mapping[str, Any] | None,
) -> dict[str, Any]:
    lines: list[dict[str, Any]] = [
        {"key": "resident", "label": "תושב ישראל", "twelfths": data.RESIDENT_TWELFTHS},
        {"key": "commute", "label": "זיכוי נסיעה לעבודה", "twelfths": data.COMMUTE_TWELFTHS},
    ]
    if gender == "woman":
        lines.append({"key": "woman", "label": "תוספת לאישה", "twelfths": data.WOMAN_TWELFTHS})
    table = data.CHILD_POINTS_TWELFTHS[gender]
    child_twelfths = total(children[band] * table[band] for band in data.CHILD_BANDS)
    if child_twelfths > 0:
        lines.append({"key": "children", "label": "ילדים", "twelfths": child_twelfths})
    if degree != "none":
        lines.append({"key": "degree", "label": DEGREE_LABELS.get(degree, "תואר שני"), "twelfths": data.DEGREE_TWELFTHS[degree]})
    oleh_twelfths = _oleh_twelfths(oleh["month"], oleh["year"]) if oleh else 0
    if oleh_twelfths > 0:
        lines.append({"key": "oleh", "label": f"עולה חדש ב-{data.TAX_YEAR}", "twelfths": oleh_twelfths})
    soldier_twelfths = (
        _soldier_twelfths(soldier["discharge"]["month"], soldier["discharge"]["year"], bool(soldier.get("full_service")))
        if soldier
        else 0
    )
    if soldier_twelfths > 0:
        lines.append({"key": "soldier", "label": f"חייל משוחרר ב-{data.TAX_YEAR}", "twelfths": soldier_twelfths})
    twelfths = total(line["twelfths"] for line in lines)
    yearly = twelfths * data.POINT_VALUE_MONTHLY
    return {"lines": lines, "twelfths": twelfths, "points": twelfths / 12, "yearly": yearly, "monthly": js_round(yearly / 12)}
