"""Portable output regressions; requires the skill's pandas/numpy dependencies."""
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SCRIPTS = Path(__file__).resolve().parent
SAMPLE = SCRIPTS.parent / "assets/test_data.csv"


@unittest.skipUnless(importlib.util.find_spec("pandas"), "pandas is required")
class OutputTests(unittest.TestCase):
    def run_pipeline(self, explicit):
        with tempfile.TemporaryDirectory(prefix="data-detective-test-") as temp:
            folder = Path(temp)
            env = {**os.environ, "TMPDIR": temp, "TEMP": temp, "TMP": temp,
                   "PYTHONIOENCODING": "utf-8", "PYTHONDONTWRITEBYTECODE": "1"}
            findings = folder / ("custom.json" if explicit else "data_detective_findings.json")
            report = folder / ("custom.html" if explicit else "data_detective_report.html")
            analyze_args = [str(SAMPLE)]
            render_args = []
            if explicit:
                analyze_args += ["--output", str(findings)]
                render_args = [str(findings), "--output", str(report)]
            for name, args in (("investigate.py", analyze_args), ("report.py", render_args)):
                result = subprocess.run([sys.executable, str(SCRIPTS / name), *args],
                                        cwd=temp, env=env, capture_output=True, text=True,
                                        encoding="utf-8", timeout=60)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            data = json.loads(findings.read_text(encoding="utf-8"))
            self.assertGreater(data["scene_survey"]["rows"], 0)
            self.assertTrue(data["summary"]["top_findings"])
            self.assertIn("<!DOCTYPE html>", report.read_text(encoding="utf-8"))

    def test_native_temporary_directory(self):
        self.run_pipeline(explicit=False)

    def test_explicit_output_paths(self):
        self.run_pipeline(explicit=True)


if __name__ == "__main__":
    unittest.main()
