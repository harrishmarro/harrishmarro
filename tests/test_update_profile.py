"""Checks for the public KPI definitions shown on the profile."""

import importlib.util
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "update_profile.py"
SPEC = importlib.util.spec_from_file_location("update_profile", SCRIPT)
profile = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(profile)


class ProfileKpiTests(unittest.TestCase):
    def test_ci_rate_and_security_status_are_labeled(self):
        ci = {"workflow_runs": [{"conclusion": "success"}] * 9 + [{"conclusion": "failure"}]}
        security = {"workflow_runs": [{"conclusion": "success",
                                       "created_at": "2026-10-30T07:00:00Z"}]}
        issues = [{"number": 1}, {"number": 2, "pull_request": {"url": "example"}}]
        svg = profile.render_engineering_svg(ci, security, issues)
        ET.fromstring(svg)
        self.assertIn("90%", svg)
        self.assertIn("9/10 recent main runs", svg)
        self.assertIn("Passing", svg)
        self.assertIn("Public issues labeled security:\n    1", svg)
        self.assertIn("Private dependency alerts are excluded", svg)

    def test_unavailable_data_is_not_reported_as_zero(self):
        svg = profile.render_engineering_svg(None, None, None)
        ET.fromstring(svg)
        self.assertIn("N/A", svg)
        self.assertIn("Public issue data unavailable", svg)


if __name__ == "__main__":
    unittest.main()
