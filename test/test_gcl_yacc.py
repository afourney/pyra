# Load what we actually need to run the tests
import unittest
from contextlib import redirect_stdout
from io import StringIO

from pyra.gcl_yacc import gcl_yacc_parse


class TestGclLex(unittest.TestCase):
    def test_errors_have_locations_and_do_not_recover_to_partial_queries(self):
        for expr, offset, message in (
            ('"word" +', 9, "Unexpected end"),
            ('("word"', 8, "Unexpected end"),
            ('"word" + + "other"', 10, "Unexpected token"),
            ("unquoted", 1, "must be quoted"),
            ('"unfinished', 1, "Unterminated"),
            ("", 1, "Unexpected end"),
        ):
            with self.subTest(expr=expr), redirect_stdout(StringIO()) as output:
                with self.assertRaises(SyntaxError) as caught:
                    gcl_yacc_parse(expr)
                self.assertIn(message, caught.exception.msg)
                self.assertEqual(caught.exception.offset, offset)
                self.assertEqual(caught.exception.text, expr)
                self.assertEqual(output.getvalue(), "")
                self.assertEqual(gcl_yacc_parse('"valid"'), ("Phrase", "valid"))

    def setUp(self):
        pass

    def test_trivial_corpus(self):
        expr = '123 .. 456 > "hello"'
        results = gcl_yacc_parse(expr)

        self.assertEqual(
            results,
            (
                "Containing",
                ("BoundedBy", ("Position", 123), ("Position", 456)),
                ("Phrase", "hello"),
            ),
        )

    def test_negative_containment(self):
        self.assertEqual(
            gcl_yacc_parse("1/>2/<3"),
            (
                "NotContainedIn",
                ("NotContaining", ("Position", 1), ("Position", 2)),
                ("Position", 3),
            ),
        )
        self.assertEqual(
            gcl_yacc_parse("1/<2/>3"),
            (
                "NotContaining",
                ("NotContainedIn", ("Position", 1), ("Position", 2)),
                ("Position", 3),
            ),
        )

    def test_negative_containment_precedence(self):
        self.assertEqual(
            gcl_yacc_parse('1 .. 2 /> "a" + "b"'),
            (
                "NotContaining",
                ("BoundedBy", ("Position", 1), ("Position", 2)),
                ("Or", ("Phrase", "a"), ("Phrase", "b")),
            ),
        )
        self.assertEqual(
            gcl_yacc_parse('"a" ^ "b" /< [5] > %1'),
            (
                "Containing",
                ("NotContainedIn", ("And", ("Phrase", "a"), ("Phrase", "b")), ("Length", 5)),
                ("Param", "1"),
            ),
        )
        self.assertEqual(
            gcl_yacc_parse("1 /> (2 /< 3)"),
            (
                "NotContaining",
                ("Position", 1),
                ("NotContainedIn", ("Position", 2), ("Position", 3)),
            ),
        )
