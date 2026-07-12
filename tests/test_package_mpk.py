import json
import os
import subprocess
import sys
import tempfile
import unittest
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIXTURE = os.path.join(ROOT, "tests", "fixture-app")
SCRIPT = os.path.join(ROOT, "package_mpk.py")


class PackageMpkTests(unittest.TestCase):
    def _build(self):
        result = subprocess.run(
            [sys.executable, SCRIPT, FIXTURE],
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip()

    def tearDown(self):
        for name in os.listdir(ROOT):
            if name.endswith(".mpk"):
                os.remove(os.path.join(ROOT, name))

    def test_builds_a_well_formed_mpk(self):
        out = self._build()
        self.assertTrue(os.path.exists(out))
        with zipfile.ZipFile(out) as z:
            names = z.namelist()
        self.assertEqual(names[0], "fixture-app/")
        self.assertIn("fixture-app/MANIFEST.JSON", names)
        self.assertIn("fixture-app/fixture_app.py", names)
        self.assertFalse(any("__pycache__" in n for n in names))

    def test_output_is_deterministic(self):
        first = self._build()
        with open(first, "rb") as f:
            first_bytes = f.read()
        os.remove(first)
        second = self._build()
        with open(second, "rb") as f:
            second_bytes = f.read()
        self.assertEqual(first_bytes, second_bytes)

    def test_fullname_mismatch_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            app_dir = os.path.join(tmp, "wrong-name")
            os.makedirs(app_dir)
            with open(os.path.join(app_dir, "MANIFEST.JSON"), "w") as f:
                json.dump({"fullname": "actual-name", "version": "1.0.0"}, f)
            result = subprocess.run(
                [sys.executable, SCRIPT, app_dir], capture_output=True, text=True
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("must match", result.stderr)


if __name__ == "__main__":
    unittest.main()
