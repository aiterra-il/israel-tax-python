from __future__ import annotations

import math
from collections.abc import Mapping
from typing import Any, Literal, Optional, TypedDict, Union

from . import _calc, _pay
from . import _data as data
from ._js import js_number, js_round, js_str

__version__ = "1.0.0"

__all__ = [
    "ANNUAL_TAX_BRACKETS",
    "CHILD_BANDS",
    "POINT_VALUE_MONTHLY",
    "STANDARD_VAT_RATE",
    "TAX_YEAR",
    "credit_points",
    "gross_for_net",
    "minimum_wage",
    "net_salary",
    "purchase_tax",
    "recuperation_pay",
    "self_employed_tax",
    "severance_pay",
    "vat",
]

TAX_YEAR: int = data.TAX_YEAR
STANDARD_VAT_RATE: int = data.STANDARD_VAT_RATE
POINT_VALUE_MONTHLY: int = data.POINT_VALUE_MONTHLY
ANNUAL_TAX_BRACKETS: tuple[dict[str, Optional[int]], ...] = data.ANNUAL_TAX_BRACKETS
CHILD_BANDS: tuple[str, ...] = data.CHILD_BANDS

Number = Union[int, float]
Gender = Literal["man", "woman"]
SeveranceRate = Literal["partial", "full"]
Buyer = Literal["single", "additional", "oleh"]

TaxRow = TypedDict(
    "TaxRow",
    {"from": Number, "to": Optional[Number], "rate_basis_points": int, "income": Number, "tax": int},
)
PurchaseRow = TypedDict(
    "PurchaseRow",
    {"from": Number, "to": Optional[int], "rate_basis_points": int, "amount": Number, "tax": int},
)


class IncomeTax(TypedDict):
    taxable: Number
    rows: list[TaxRow]
    surtax_threshold: Number
    surtax_income: Number
    surtax: int
    gross: Number
    credit_points_hundredths: Number
    credit_value: int
    credit_used: Number
    net: Number


class EmployeeBtl(TypedDict):
    base: Number
    reduced_part: Number
    full_part: Number
    national: int
    health: int
    total: int


class EmployerCost(TypedDict):
    btl: int
    pension: int
    severance: int
    severance_basis_points: int
    hishtalmut: int
    total: int
    cost: int


class Salary(TypedDict):
    gross: int
    hishtalmut_benefit: int
    taxable: int
    income_tax: IncomeTax
    pension_credit: Number
    tax: Number
    btl: EmployeeBtl
    pension: int
    hishtalmut: int
    deductions: Number
    net: Number
    employer: EmployerCost


class Vat(TypedDict):
    net: float
    vat: float
    gross: float
    rate: float


class PurchaseTax(TypedDict):
    kind: str
    value: int
    rows: list[PurchaseRow]
    tax: Number
    effective_rate: float
    oleh_benefit_denied: bool
    saving_versus_single: Number


class SelfEmployedBtl(TypedDict):
    base: Number
    reduced_limit: Number
    reduced_part: Number
    full_part: Number
    national_reduced: int
    national_full: int
    health_reduced: int
    health_full: int
    national: int
    health: int
    total: int
    deductible: Number
    minimum_applied: bool
    ceiling_applied: bool


class SelfEmployedTax(TypedDict):
    months: Number
    revenue: int
    expenses: int
    profit: int
    loss: bool
    btl: SelfEmployedBtl
    income_tax: IncomeTax
    total: Number
    net: Number
    effective_rate: float
    marginal_rate_basis_points: int
    advance_rate: float


class Tenure(TypedDict):
    months: int
    extra_days: int
    years: float


class Severance(TypedDict):
    kind: Literal["result"]
    tenure: Tenure
    salary: float
    eligible_by_seniority: bool
    section14: str
    severance: Number
    exempt: Optional[Number]
    taxable: Optional[Number]
    end_year: int
    start_day: int
    end_day: int


class CreditLine(TypedDict):
    key: str
    label: str
    twelfths: Number


class CreditPoints(TypedDict):
    lines: list[CreditLine]
    twelfths: Number
    points: float
    yearly: Number
    monthly: int


class MonthYear(TypedDict):
    month: int
    year: int


class _SoldierRequired(TypedDict):
    discharge: MonthYear


class Soldier(_SoldierRequired, total=False):
    full_service: bool


class Recuperation(TypedDict):
    kind: Literal["result"]
    year: Number
    table_days: Number
    months: Number
    percent: float
    rate: float
    days: float
    amount: float
    top_up: Optional[float]


class DailyMinimum(TypedDict):
    five_day_week: float
    six_day_week: float


class MinimumWage(TypedDict):
    period: str
    monthly: float
    hourly: float
    daily: Optional[DailyMinimum]


def _require_amount(value: Any, name: str) -> float:
    number = js_number(value)
    if not math.isfinite(number) or number < 0:
        raise ValueError(f"{name} must be a non-negative number of shekels")
    return number


def _whole(value: float) -> int:
    return js_round(value)


def _to_agorot(shekels: float) -> int:
    return js_round(shekels * 100)


def _credit_hundredths(points: Optional[Number], gender: str) -> int:
    if points is None:
        return data.DEFAULT_CREDIT_POINTS[_known(gender, data.DEFAULT_CREDIT_POINTS, "gender")]
    return js_round(js_number(points) * 100)


def _known(value: str, options: Mapping[str, Any], name: str) -> str:
    if value not in options:
        raise ValueError(f"{name} must be one of: {', '.join(options)}")
    return value


def net_salary(
    gross: Number,
    *,
    credit_points: Optional[Number] = None,
    gender: Gender = "man",
    hishtalmut: bool = False,
    severance: SeveranceRate = "partial",
) -> Salary:
    result: Any = _calc.salary(
        _whole(_require_amount(gross, "gross")),
        _credit_hundredths(credit_points, gender),
        hishtalmut,
        _known(severance, data.SEVERANCE_BASIS_POINTS, "severance"),
    )
    return result


def gross_for_net(
    net: Number,
    *,
    credit_points: Optional[Number] = None,
    gender: Gender = "man",
    hishtalmut: bool = False,
    severance: SeveranceRate = "partial",
) -> Optional[int]:
    return _calc.gross_for_net(
        _whole(_require_amount(net, "net")),
        _credit_hundredths(credit_points, gender),
        hishtalmut,
        _known(severance, data.SEVERANCE_BASIS_POINTS, "severance"),
    )


def vat(amount: Number, *, mode: Literal["add", "extract"] = "add", rate: Number = STANDARD_VAT_RATE) -> Vat:
    result = _calc.vat_breakdown(
        _to_agorot(_require_amount(amount, "amount")),
        mode,
        js_round(js_number(rate) * 100),
    )
    return {
        "net": result["net"] / 100,
        "vat": result["vat"] / 100,
        "gross": result["gross"] / 100,
        "rate": js_number(rate),
    }


def purchase_tax(value: Number, buyer: Buyer = "single") -> PurchaseTax:
    result: Any = _calc.purchase_tax(_to_agorot(_require_amount(value, "value")), buyer)
    return result


def self_employed_tax(
    revenue: Number,
    *,
    expenses: Number = 0,
    credit_points: Optional[Number] = None,
    gender: Gender = "man",
    months: Number = 12,
) -> SelfEmployedTax:
    result: Any = _calc.self_employed(
        _to_agorot(_require_amount(revenue, "revenue")),
        _to_agorot(_require_amount(expenses, "expenses")),
        _credit_hundredths(credit_points, gender),
        months,
    )
    return result


def severance_pay(
    start: str,
    end: str,
    salary: Union[Number, str],
    *,
    section14: Literal["none", "partial", "full"] = "none",
) -> Severance:
    result: Any = _calc.severance(start, end, js_str(salary), section14)
    return result


def credit_points(
    *,
    gender: Gender = "man",
    children: Optional[Mapping[str, Number]] = None,
    degree: Literal["none", "first", "second"] = "none",
    oleh: Optional[MonthYear] = None,
    soldier: Optional[Soldier] = None,
) -> CreditPoints:
    given = children or {}
    unknown = set(given) - set(data.CHILD_BANDS)
    if unknown:
        raise ValueError(f"children keys must be among: {', '.join(data.CHILD_BANDS)}")
    counts = {band: js_number(given.get(band, 0)) for band in data.CHILD_BANDS}
    result: Any = _calc.credits(
        _known(gender, data.CHILD_POINTS_TWELFTHS, "gender"),
        counts,
        degree if degree == "none" else _known(degree, data.DEGREE_TWELFTHS, "degree"),
        oleh,
        soldier,
    )
    return result


def recuperation_pay(
    seniority_year: int,
    *,
    months: Number = 12,
    job_percent: Number = 100,
    day_rate: Number = data.DAY_RATE_AGOROT / 100,
) -> Recuperation:
    result = _pay.recuperation(js_str(seniority_year), js_str(months), js_str(job_percent), js_str(day_rate))
    top_up = result["top_up"]
    output: Any = {
        **result,
        "amount": result["amount"] / 100,
        "rate": result["rate"] / 100,
        "percent": result["percent"] / 100,
        "top_up": None if top_up is None else top_up / 100,
    }
    return output


def minimum_wage(*, age: str = "adult", period: str = data.CURRENT_PERIOD) -> MinimumWage:
    return {
        "period": period,
        "monthly": _pay.full_monthly(period, age) / 100,
        "hourly": _pay.hourly_rate(period, age) / 100,
        "daily": (
            {
                "five_day_week": _pay.daily_rate(period, "5") / 100,
                "six_day_week": _pay.daily_rate(period, "6") / 100,
            }
            if age == "adult"
            else None
        ),
    }
