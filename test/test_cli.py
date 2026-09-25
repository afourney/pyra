import contextlib
import io
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from pyra import InvertedIndex, RegexTokenizer, StringTextSource
from pyra.cli import _preview, _shorten, _show_results, main, run_shell


class TerminalOutput(io.StringIO):
    def isatty(self):
        return True


class TestCLI(unittest.TestCase):
    def test_cli_uses_markup_and_lowercase_for_file_and_ranked_queries(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "notes.xml"
            path.write_text("<TITLE>Straße & FOX</TITLE>", encoding="utf-8")
            output = io.StringIO()
            with (
                contextlib.redirect_stdout(output),
                patch(
                    "builtins.input",
                    side_effect=['"<title>".."</title>"', "? STRAßE", "? STRASSE", EOFError],
                ),
            ):
                self.assertEqual(main([str(path)]), 0)
            self.assertIn("1. [0:4] <TITLE>Straße & FOX</TITLE>", output.getvalue())
            self.assertIn("1. [1:2] <TITLE>Straße & FOX</TITLE>", output.getvalue())
            self.assertEqual(output.getvalue().count("No results."), 1)

    def setUp(self):
        self.source = StringTextSource("Before the BROWN, Fox jumps after lunch.")
        self.index = InvertedIndex(self.source)
        self.reader = self.source.reader(self.index)

    def test_installed_commands_from_another_directory(self):
        executable = shutil.which("pyra")
        self.assertIsNotNone(executable)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "notes.txt"
            path.write_text("Before the BROWN, Fox jumps after lunch.", encoding="utf-8")
            for command in ([executable], [sys.executable, "-I", "-m", "pyra"]):
                with self.subTest(command=command):
                    result = subprocess.run(
                        [*command, str(path)],
                        input='"brown", "fox"\n? BROWN, Fox\n"missing"\n',
                        text=True,
                        capture_output=True,
                        cwd=directory,
                        timeout=10,
                        check=True,
                    )
                    self.assertEqual(result.stderr, "")
                    self.assertIn("1. [2:4] BROWN, Fox\n", result.stdout)
                    self.assertIn("Before the BROWN, Fox jumps after lunch", result.stdout)
                    self.assertIn("No results.", result.stdout)
                    self.assertNotIn("Traceback", result.stdout)

    def test_errors_and_interrupts_leave_shell_usable(self):
        output = io.StringIO()
        inputs = [
            "",
            '"brown" +',
            "unquoted",
            "%1",
            "? !!!",
            KeyboardInterrupt,
            '"fox"',
            EOFError,
        ]
        with contextlib.redirect_stdout(output), patch("builtins.input", side_effect=inputs):
            run_shell(self.index, self.reader, RegexTokenizer())
        text = output.getvalue()
        self.assertIn("Unexpected end of query", text)
        self.assertIn("search terms must be quoted", text)
        self.assertIn("Unbound parameter", text)
        self.assertIn("^", text)
        self.assertIn("Enter search terms", text)
        self.assertIn("Cancelled.", text)
        self.assertIn("1. [3:4] Fox", text)
        self.assertNotIn("Traceback", text)

    def test_preview_preserves_exact_gcl_match_and_adds_ranked_context(self):
        region = slice(2, 4)
        self.assertEqual(_preview(self.reader, region, 7, context=False), "BROWN, Fox")
        self.assertEqual(
            _preview(self.reader, region, 7, context=True),
            "Before the BROWN, Fox jumps after lunch",
        )

    def test_long_preview_retains_both_ends_and_avoids_reading_the_middle(self):
        source = StringTextSource("Beginning " + "middle " * 10000 + "ending")
        index = InvertedIndex(source)
        with patch.object(source, "read", wraps=source.read) as read:
            preview = _preview(
                source.reader(index),
                slice(0, index.corpus_length),
                index.corpus_length,
                context=False,
            )
        self.assertLessEqual(len(preview), 300)
        self.assertTrue(preview.startswith("Beginning"))
        self.assertTrue(preview.endswith("ending"))
        self.assertIn(" … ", preview)
        self.assertLess(sum(call.args[1] - call.args[0] for call in read.call_args_list), 3000)

    def test_preview_collapses_whitespace_and_removes_terminal_controls(self):
        self.assertEqual(_shorten("hello\n\tworld"), "hello world")
        self.assertNotIn("\x1b", _shorten("hello\x1b[2J world"))
        self.assertEqual(_shorten("small, intact passage"), "small, intact passage")
        self.assertLessEqual(len(_shorten("x" * 1000)), 300)

    def display(self, count, keys, *, height=100, interactive=True):
        source = StringTextSource("word " * count)
        index = InvertedIndex(source)
        output = TerminalOutput() if interactive else io.StringIO()
        with (
            contextlib.redirect_stdout(output),
            patch("pyra.cli.sys.stdin.isatty", return_value=interactive),
            patch("pyra.cli.shutil.get_terminal_size", return_value=os.terminal_size((80, height))),
            patch("pyra.cli._read_key", side_effect=keys) as key,
        ):
            _show_results(
                (slice(i, i + 1) for i in range(count)), source.reader(index), count, ranked=False
            )
        return output.getvalue(), key.call_count

    def test_space_advances_and_another_key_stops(self):
        text, calls = self.display(25, [" ", "q"])
        self.assertIn("20. [19:20] word", text)
        self.assertNotIn("21. [20:21]", text)
        self.assertEqual(calls, 2)

    def test_exact_page_does_not_prompt(self):
        text, calls = self.display(10, [])
        self.assertIn("10. [9:10] word", text)
        self.assertNotIn("Space:", text)
        self.assertEqual(calls, 0)

    def test_short_terminal_uses_smaller_pages(self):
        text, calls = self.display(10, ["x"], height=10)
        self.assertIn("3. [2:3] word", text)
        self.assertNotIn("4. [3:4]", text)
        self.assertEqual(calls, 1)

    def test_redirected_output_never_reads_paging_keys(self):
        text, calls = self.display(11, [], interactive=False)
        self.assertIn("10. [9:10] word", text)
        self.assertNotIn("11. [10:11]", text)
        self.assertIn("More results available", text)
        self.assertEqual(calls, 0)

    def test_empty_file(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "empty.txt"
            path.touch()
            output = io.StringIO()
            with (
                contextlib.redirect_stdout(output),
                patch("builtins.input", side_effect=['"word"', "? word", EOFError]),
            ):
                self.assertEqual(main([str(path)]), 0)
            self.assertEqual(output.getvalue().count("No results."), 2)

    def test_invalid_utf8_is_a_clear_startup_error(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "binary.txt"
            path.write_bytes(b"\xff")
            errors = io.StringIO()
            with contextlib.redirect_stderr(errors), contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(main([str(path)]), 1)
            self.assertIn("utf-8", errors.getvalue())
            self.assertNotIn("Traceback", errors.getvalue())

    def test_missing_file_is_a_clear_usage_error(self):
        with tempfile.TemporaryDirectory() as directory:
            errors = io.StringIO()
            with contextlib.redirect_stderr(errors), self.assertRaises(SystemExit) as caught:
                main([str(Path(directory) / "missing.txt")])
            self.assertEqual(caught.exception.code, 2)
            self.assertIn("not a regular file", errors.getvalue())
