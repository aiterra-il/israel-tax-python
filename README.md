# israel-tax · מחשבוני מס ושכר בישראל 2026

[![PyPI](https://img.shields.io/pypi/v/israel-tax?color=2447D6)](https://pypi.org/project/israel-tax/)
[![tests](https://github.com/aiterra-il/israel-tax-python/actions/workflows/tests.yml/badge.svg)](https://github.com/aiterra-il/israel-tax-python/actions/workflows/tests.yml)
[![license](https://img.shields.io/badge/license-MIT-3E96F9)](LICENSE)
![dependencies](https://img.shields.io/badge/dependencies-0-060B22)

Israeli tax and payroll calculators with the 2026 rates, for Python: net salary from gross, gross from net, VAT at 18%, purchase tax on a home, self-employed income tax and National Insurance, severance pay, credit points, recuperation pay and the minimum wage.

This is the Python edition of the [israel-tax](https://www.npmjs.com/package/israel-tax) package on npm. The rates, brackets and rounding are the same, and the tests compare every function with the answers of the JavaScript version on more than 1,900 inputs.

- **Payroll and HR systems.** Net salary with income tax, credit points, National Insurance, health tax, pension and study fund, and the full employer cost.
- **Offers and contracts.** `gross_for_net()` finds the gross salary that gives a wanted net.
- **Invoices, real estate and freelancers.** VAT both ways, purchase tax by bracket, an estimate of a self-employed person's tax.

## Install

```bash
pip install israel-tax
```

No dependencies. Python 3.10 or newer. Type hints included.

## Use

```python
from israel_tax import (
    credit_points, gross_for_net, minimum_wage, net_salary, purchase_tax,
    recuperation_pay, self_employed_tax, severance_pay, vat,
)

salary = net_salary(15000)
salary["tax"], salary["pension"], salary["net"], salary["employer"]["cost"]
# (1333, 900, 11550, 17777)

gross_for_net(10000)
# 12494

vat(100)
# {'net': 100.0, 'vat': 18.0, 'gross': 118.0, 'rate': 18.0}
vat(118, mode="extract")["net"]
# 100.0

purchase_tax(2_500_000)["tax"]
# 20538

result = self_employed_tax(300000, expenses=60000)
result["profit"], result["total"], result["net"]
# (240000, 60349, 179651)

severance_pay("2020-01-01", "2025-12-31", 12000)["severance"]
# 72000.0

credit_points(gender="woman", children={"six_seventeen": 2})["points"]
# 6.75

recuperation_pay(3)["amount"]
# 2709.0

minimum_wage()
# {'period': '2026', 'monthly': 6443.85, 'hourly': 35.4,
#  'daily': {'five_day_week': 297.4, 'six_day_week': 257.75}}
```

Every result is a plain `dict` described by a `TypedDict`, with the full breakdown: the tax brackets, National Insurance by part, the credit points used, the employer side.

## API

| Function | What it returns | On the site |
|---|---|---|
| `net_salary(gross, *, credit_points, gender, hishtalmut, severance)` | Net salary, every deduction and the employer cost | [net salary calculator](https://www.aiterra.co.il/tools/net-salary-calculator) |
| `gross_for_net(net, ...)` | The lowest gross that gives this net, or `None` when a gross of 1,000,000 ₪ is not enough | [net salary calculator](https://www.aiterra.co.il/tools/net-salary-calculator) |
| `vat(amount, *, mode="add", rate=18)` | Amount before VAT, VAT and total, in shekels | [VAT calculator](https://www.aiterra.co.il/tools/vat-calculator) |
| `purchase_tax(value, buyer="single")` | Purchase tax by bracket for `single`, `additional` or `oleh` | [purchase tax calculator](https://www.aiterra.co.il/tools/purchase-tax-calculator) |
| `self_employed_tax(revenue, *, expenses, credit_points, gender, months)` | Income tax, National Insurance and health tax of a self-employed person | [self-employed tax calculator](https://www.aiterra.co.il/tools/self-employed-tax-calculator) |
| `severance_pay(start, end, salary, *, section14)` | Severance by the law, tenure, and the 2026 tax exemption | [severance pay calculator](https://www.aiterra.co.il/tools/severance-pay-calculator) |
| `credit_points(*, gender, children, degree, oleh, soldier)` | Credit points for 2026 and their value | [credit points calculator](https://www.aiterra.co.il/tools/tax-credit-points-calculator) |
| `recuperation_pay(seniority_year, *, months, job_percent, day_rate)` | Recuperation days and pay in the private sector | [recuperation pay calculator](https://www.aiterra.co.il/tools/recuperation-pay-calculator) |
| `minimum_wage(*, age, period)` | Minimum wage per month, hour and day | [minimum wage 2026](https://www.aiterra.co.il/tools/minimum-wage-2026) |

Amounts are in shekels. `credit_points` takes points, for example `2.25`; without it the default for the gender is used. Children are counted by age band: `birth`, `to_two`, `three`, `four_five`, `six_seventeen`, `eighteen`. `oleh` and `soldier` take a month and year: `{"month": 3, "year": 2025}` and `{"discharge": {"month": 6, "year": 2025}, "full_service": True}`.

Invalid input raises `ValueError`. The messages of `severance_pay` and `recuperation_pay` are in Hebrew, as on the site.

## Limits

- The rates are those of 2026, checked against the Israel Tax Authority, National Insurance and Kol Zchut in October 2026. A new tax year needs a new version.
- The results are estimates for one regular job or one business, not tax advice.
- Recuperation pay follows the general extension order of the private sector. The public sector and branch agreements are different.

## The same calculators elsewhere

- JavaScript: [israel-tax on npm](https://www.npmjs.com/package/israel-tax).
- In the browser: [the free Israeli tax calculators on aiterra.co.il](https://www.aiterra.co.il/tools/net-salary-calculator).

<div dir="rtl">

## בעברית

מחשבוני מס ושכר לפי השיעורים של 2026, לפייתון: שכר נטו מברוטו, ברוטו מנטו, מע״מ 18%, מס רכישה לדירה, מס הכנסה וביטוח לאומי לעצמאי, פיצויי פיטורים, נקודות זיכוי, דמי הבראה ושכר מינימום.

זו גרסת הפייתון של חבילת [israel-tax](https://www.npmjs.com/package/israel-tax) ב-npm. המדרגות, השיעורים והעיגול זהים, והבדיקות משוות כל פונקציה לתשובות של גרסת ה-JavaScript.

- **מערכות שכר ומשאבי אנוש.** נטו עם מס הכנסה, נקודות זיכוי, ביטוח לאומי, מס בריאות, פנסיה וקרן השתלמות, ועלות המעביד.
- **הצעות שכר.** `gross_for_net()` מוצאת את הברוטו שנותן את הנטו המבוקש.
- **חשבוניות, נדל״ן ועצמאים.** מע״מ לשני הכיוונים, מס רכישה לפי מדרגות והערכת מס לעצמאי.

התוצאות הן הערכה ולא ייעוץ מס. המחשבונים נבנו ב-[Aiterra](https://www.aiterra.co.il) בשביל [מחשבון השכר נטו החינמי באתר](https://www.aiterra.co.il/tools/net-salary-calculator).

</div>

## Licence

MIT. Built by [Aiterra](https://www.aiterra.co.il), a software studio in Israel that builds AI agents, voice agents and websites.
