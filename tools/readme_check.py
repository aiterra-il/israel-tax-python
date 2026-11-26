import sys

from israel_tax import (
    credit_points,
    gross_for_net,
    minimum_wage,
    net_salary,
    purchase_tax,
    recuperation_pay,
    self_employed_tax,
    severance_pay,
    vat,
)

sys.stdout.reconfigure(encoding="utf-8")

salary = net_salary(15000)
print((salary["tax"], salary["pension"], salary["net"], salary["employer"]["cost"]))
print(gross_for_net(10000))
print(vat(100))
print(vat(118, mode="extract")["net"])
print(purchase_tax(2_500_000)["tax"])
result = self_employed_tax(300000, expenses=60000)
print((result["profit"], result["total"], result["net"]))
print(severance_pay("2020-01-01", "2025-12-31", 12000)["severance"])
print(credit_points(gender="woman", children={"six_seventeen": 2})["points"])
print(recuperation_pay(3)["amount"])
print(minimum_wage())
