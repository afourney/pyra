import os
import re
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
        self.assertIn("Example queries:", result.stdout)
        self.assertIn("Return short play titles", result.stdout)
        self.assertIn("? search terms", result.stdout)
        matches = re.findall(r"\d+\. \[\d+:\d+\] ([^\n]+)", result.stdout)
        self.assertEqual(
            matches,
            ["<TITLE>The Tragedy of Hamlet, Prince of Denmark</TITLE>"],
        )
