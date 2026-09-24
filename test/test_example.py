import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


class TestExample(unittest.TestCase):
    def test_shakespeare_query_from_another_directory(self):
        root = Path(__file__).resolve().parents[1]
        env = os.environ.copy()
        env["PYTHONPATH"] = str(root)
        query = (
            '(("<title>".."</title>") < ("<play>".."</title>"))'
            ' < (("<play>".."</play>")'
            ' > ("to", "be", "or", "not", "to", "be"))\n'
        )
        with tempfile.TemporaryDirectory() as cwd:
            result = subprocess.run(
                [sys.executable, str(root / "examples" / "gcl_shell.py")],
                input=query,
                text=True,
                capture_output=True,
                cwd=cwd,
                env=env,
                timeout=60,
                check=True,
            )
        self.assertNotIn("Traceback", result.stdout)
        self.assertEqual(result.stderr, "")
        matches = [line for line in result.stdout.splitlines() if line.startswith("slice(")]
        self.assertEqual(
            matches,
            [("slice(239304,239313):\t<title> the tragedy of hamlet prince of denmark </title>")],
        )
