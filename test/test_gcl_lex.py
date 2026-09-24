# Load what we actually need to run the tests
import unittest

from pyra.gcl_lex import gcl_lex


class TestGclLex(unittest.TestCase):
    def setUp(self):
        pass

    def test_trivial_corpus(self):
        expr = "123 ... 456"
        results = gcl_lex(expr)

        self.assertEqual(
            results,
            [
                ("'INT'", "123"),
                ("'OP_BOUNDED_BY'", "'...'"),
                ("'INT'", "456"),
            ],
        )

    def test_negative_containment(self):
        expr = "1/>2/<3 > 4 < 5"
        results = gcl_lex(expr)

        self.assertEqual(
            results,
            [
                ("'INT'", "1"),
                ("'OP_NOT_CONTAINING'", "'/>'"),
                ("'INT'", "2"),
                ("'OP_NOT_CONTAINED_IN'", "'/<'"),
                ("'INT'", "3"),
                ("'OP_CONTAINING'", "'>'"),
                ("'INT'", "4"),
                ("'OP_CONTAINED_IN'", "'<'"),
                ("'INT'", "5"),
            ],
        )

        self.assertEqual(
            gcl_lex('"/>" "/<"'),
            [
                ("'STRING'", "'/>'"),
                ("'STRING'", "'/<'"),
            ],
        )
