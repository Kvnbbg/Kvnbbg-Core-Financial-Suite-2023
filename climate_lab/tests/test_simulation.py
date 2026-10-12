"""Reproducible unit tests for the toy climate stress simulator."""
import math
import unittest

from server import InputError, SCENARIOS, simulate


def sample_payload():
    return {
        "scenario": "orderly_transition",
        "horizon_years": 10,
        "portfolio": [
            {"sector": "energy", "value": 100_000, "emissions_intensity": 0.8},
            {"sector": "technology", "value": 50_000, "emissions_intensity": 0.1},
        ],
    }


class SimulationTests(unittest.TestCase):
    def test_result_is_deterministic_and_totals_reconcile(self):
        first = simulate(sample_payload())
        second = simulate(sample_payload())
        self.assertEqual(first, second)
        self.assertEqual(first["portfolio_value"], 150_000)
        self.assertAlmostEqual(
            sum(row["estimated_loss"] for row in first["positions"]),
            first["estimated_loss"],
            places=2,
        )
        self.assertGreaterEqual(first["estimated_loss_pct"], 0)
        self.assertLessEqual(first["estimated_loss_pct"], 95)

    def test_all_documented_scenarios_are_accepted(self):
        for scenario in SCENARIOS:
            payload = sample_payload()
            payload["scenario"] = scenario
            self.assertEqual(simulate(payload)["scenario"], scenario)

    def test_unknown_scenario_is_rejected(self):
        payload = sample_payload()
        payload["scenario"] = "guaranteed_profit"
        with self.assertRaises(InputError):
            simulate(payload)

    def test_unknown_sector_is_rejected(self):
        payload = sample_payload()
        payload["portfolio"][0]["sector"] = "unmapped_sector"
        with self.assertRaises(InputError):
            simulate(payload)

    def test_negative_and_non_finite_values_are_rejected(self):
        for bad_value in (-1, float("nan"), float("inf"), True):
            payload = sample_payload()
            payload["portfolio"][0]["value"] = bad_value
            with self.subTest(value=bad_value):
                with self.assertRaises(InputError):
                    simulate(payload)

    def test_intensity_bounds_are_enforced(self):
        payload = sample_payload()
        payload["portfolio"][0]["emissions_intensity"] = 2.01
        with self.assertRaises(InputError):
            simulate(payload)

    def test_horizon_must_be_supported_integer(self):
        for bad_horizon in (0, 2, 10.0, True, 100):
            payload = sample_payload()
            payload["horizon_years"] = bad_horizon
            with self.subTest(horizon=bad_horizon):
                with self.assertRaises(InputError):
                    simulate(payload)

    def test_empty_or_oversized_portfolio_is_rejected(self):
        payload = sample_payload()
        payload["portfolio"] = []
        with self.assertRaises(InputError):
            simulate(payload)
        payload["portfolio"] = [{"sector": "energy", "value": 1}] * 101
        with self.assertRaises(InputError):
            simulate(payload)

    def test_zero_exposure_has_zero_loss(self):
        payload = {"scenario": "hot_house_world", "horizon_years": 30,
                   "portfolio": [{"sector": "energy", "value": 0, "emissions_intensity": 1}]}
        result = simulate(payload)
        self.assertEqual(result["portfolio_value"], 0)
        self.assertEqual(result["estimated_loss"], 0)
        self.assertEqual(result["estimated_loss_pct"], 0)

    def test_non_object_payload_is_rejected(self):
        with self.assertRaises(InputError):
            simulate([])


if __name__ == "__main__":
    unittest.main()
