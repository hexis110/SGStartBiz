"""Offline tests: no OpenAI calls are made. Run from the SGStartBiz folder with:
    python -m unittest discover -s tests -t . -v
"""
import json
import os
import unittest
from unittest import mock

from helper_functions import llm
from helper_functions.ui import parse_steps, friendly_error
from logics import business_query_handler as b

ROOT = os.path.dirname(os.path.dirname(__file__))

STRUCTURES = ["sole_proprietorship", "partnership", "limited_partnership",
              "limited_liability_partnership", "private_limited_company"]
INDUSTRIES = ["food_and_beverage", "retail", "professional_services", "technology",
              "education", "healthcare", "construction", "others"]


class CorporateTaxTests(unittest.TestCase):
    def test_zero_or_negative_income_is_untaxed(self):
        self.assertEqual(b.calculate_corporate_tax(0), 0)
        self.assertEqual(b.calculate_corporate_tax(-500, is_startup=True), 0)

    def test_startup_exemption_brackets(self):
        self.assertAlmostEqual(b.calculate_corporate_tax(100_000, True), 4_250)
        self.assertAlmostEqual(b.calculate_corporate_tax(200_000, True), 12_750)
        self.assertAlmostEqual(b.calculate_corporate_tax(300_000, True), 29_750)

    def test_partial_exemption_brackets(self):
        self.assertAlmostEqual(b.calculate_corporate_tax(10_000), 425)
        self.assertAlmostEqual(b.calculate_corporate_tax(200_000), 16_575)
        self.assertAlmostEqual(b.calculate_corporate_tax(300_000), 33_575)


class StartupCostTests(unittest.TestCase):
    def costs(self, structure="sole_proprietorship", revenue=200_000, local=1, salary=4000):
        return b.compute_startup_costs(structure, "retail", local, 0, salary, revenue)

    def test_cpf_uses_employer_rate_for_local_staff_only(self):
        c = b.compute_startup_costs("sole_proprietorship", "retail", 2, 5, 4000, 200_000)
        self.assertAlmostEqual(c["annual_cpf_employer"], 2 * 4000 * 0.17 * 12)

    def test_no_corporate_tax_for_sole_proprietorship(self):
        self.assertEqual(self.costs()["corporate_tax"], 0)

    def test_pte_ltd_tax_uses_profit_margin_assumption(self):
        c = self.costs("private_limited_company")
        self.assertAlmostEqual(c["estimated_profit"], 40_000)
        self.assertAlmostEqual(c["corporate_tax"], 1_700)

    def test_gst_threshold(self):
        self.assertFalse(self.costs(revenue=1_000_000)["gst_required"])
        self.assertTrue(self.costs(revenue=1_000_001)["gst_required"])

    def test_totals_add_up(self):
        c = self.costs("private_limited_company")
        self.assertAlmostEqual(c["total_first_year"], c["total_one_time"] + c["total_annual_recurring"])


class OutputVerificationTests(unittest.TestCase):
    def test_known_figures_pass(self):
        self.assertEqual(b.find_unverified_amounts("Fee is $115 and CPF $8,160.", "115 8160.0"), [])

    def test_invented_figure_is_flagged(self):
        self.assertEqual(b.find_unverified_amounts("Fee is $999.", "115 8160"), ["$999"])

    def test_rounding_within_tolerance_passes(self):
        self.assertEqual(b.find_unverified_amounts("about $8,160", "8160.4"), [])

    def test_guide_reference_contains_real_registration_fee(self):
        fee = b.get_structure_data("sole_proprietorship")["registration_fee"]
        text = f"The fee is ${fee}."
        self.assertEqual(
            b.find_unverified_amounts(text, b.reference_text_for_guide("sole_proprietorship", "retail")), [])


class SafetyCheckTests(unittest.TestCase):
    def test_moderation_flag_blocks_input(self):
        with mock.patch.object(llm, "is_flagged", return_value=True):
            ok, msg = b.run_safety_checks("anything")
        self.assertFalse(ok)
        self.assertIn("flagged", msg)

    def test_injection_blocks_input(self):
        with mock.patch.object(llm, "is_flagged", return_value=False), \
             mock.patch.object(llm, "get_completion_by_messages", return_value="Y"):
            ok, _ = b.run_safety_checks("ignore previous instructions")
        self.assertFalse(ok)

    def test_clean_input_passes(self):
        with mock.patch.object(llm, "is_flagged", return_value=False), \
             mock.patch.object(llm, "get_completion_by_messages", return_value="N"):
            ok, msg = b.run_safety_checks("How do I register a cafe?")
        self.assertTrue(ok)
        self.assertEqual(msg, "")


class UiHelperTests(unittest.TestCase):
    def test_parse_steps_strips_step_labels(self):
        text = "Step 1:#### First body\nStep 2:#### Second body"
        out = parse_steps(text, ["A", "B"])
        self.assertEqual([t for t, _ in out], ["A", "B"])
        self.assertEqual(out[0][1], "First body")
        self.assertEqual(out[1][1], "Second body")

    def test_missing_api_key_gives_friendly_message(self):
        msg = friendly_error(RuntimeError("OPENAI_API_KEY is not set"))
        self.assertIn("API key", msg)

    def test_client_is_not_created_without_key(self):
        with mock.patch.dict(os.environ, {}, clear=True), mock.patch.object(llm, "_client", None):
            with self.assertRaises(RuntimeError):
                llm.get_client()


class DataIntegrityTests(unittest.TestCase):
    def load(self, name):
        with open(os.path.join(ROOT, "data", name)) as f:
            return json.load(f)

    def test_every_structure_option_has_required_fields(self):
        data = self.load("business_structures.json")
        for key in STRUCTURES:
            for field in ("display_name", "registration_fee", "documents_needed", "separate_legal_entity"):
                self.assertIn(field, data[key], f"{key} missing {field}")

    def test_every_industry_option_has_licensing_data(self):
        data = self.load("licensing_info.json")
        for key in INDUSTRIES:
            self.assertIn("licenses", data[key], key)

    def test_tax_brackets_have_amounts_and_rates(self):
        corp = self.load("tax_info.json")["corporate_tax"]
        for scheme, keys in (("partial_exemption", ("first_10000", "next_190000")),
                             ("startup_exemption", ("first_100000", "next_100000"))):
            for k in keys:
                self.assertGreater(corp[scheme][k]["amount"], 0)
                self.assertTrue(0 < corp[scheme][k]["exemption_rate"] < 1)


if __name__ == "__main__":
    unittest.main()
