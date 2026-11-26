from __future__ import annotations

import json
import unittest
from pathlib import Path

import israel_tax

FIXTURES = json.loads(Path(__file__).with_name("fixtures.json").read_text(encoding="utf-8"))


class ParityTest(unittest.TestCase):
    def check(self, name: str) -> None:
        function = getattr(israel_tax, name)
        cases = FIXTURES[name]
        self.assertGreater(len(cases), 0)
        for case in cases:
            label = f"{name}({case['args']!r}, {case['kwargs']!r})"
            if "error" in case:
                with self.assertRaises(ValueError, msg=label) as raised:
                    function(*case["args"], **case["kwargs"])
                self.assertEqual(str(raised.exception), case["error"], label)
                continue
            self.assertEqual(function(*case["args"], **case["kwargs"]), case["result"], label)

    def test_net_salary(self):
        self.check("net_salary")

    def test_gross_for_net(self):
        self.check("gross_for_net")

    def test_vat(self):
        self.check("vat")

    def test_purchase_tax(self):
        self.check("purchase_tax")

    def test_self_employed_tax(self):
        self.check("self_employed_tax")

    def test_severance_pay(self):
        self.check("severance_pay")

    def test_credit_points(self):
        self.check("credit_points")

    def test_recuperation_pay(self):
        self.check("recuperation_pay")

    def test_minimum_wage(self):
        self.check("minimum_wage")


class BehaviourTest(unittest.TestCase):
    def test_constants(self):
        self.assertEqual(israel_tax.TAX_YEAR, 2026)
        self.assertEqual(israel_tax.STANDARD_VAT_RATE, 18)
        self.assertEqual(israel_tax.POINT_VALUE_MONTHLY, 242)
        self.assertEqual(israel_tax.ANNUAL_TAX_BRACKETS[0], {"up_to": 84120, "rate_basis_points": 1000})

    def test_net_salary_adds_up(self):
        salary = israel_tax.net_salary(15000)
        self.assertEqual(salary["net"], salary["gross"] - salary["deductions"])
        self.assertTrue(11000 < salary["net"] < 12000)

    def test_vat_both_ways(self):
        self.assertEqual(israel_tax.vat(100), {"net": 100, "vat": 18, "gross": 118, "rate": 18})
        self.assertEqual(israel_tax.vat(118, mode="extract")["net"], 100)

    def test_unknown_options_are_rejected(self):
        with self.assertRaises(ValueError):
            israel_tax.net_salary(10000, gender="other")
        with self.assertRaises(ValueError):
            israel_tax.credit_points(children={"toTwo": 1})

    def test_package_is_typed_and_versioned(self):
        self.assertTrue(Path(israel_tax.__file__).with_name("py.typed").exists())
        self.assertRegex(israel_tax.__version__, r"^\d+\.\d+\.\d+$")


if __name__ == "__main__":
    unittest.main()
