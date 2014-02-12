# Load what we actually need to run the tests
import unittest
from pyra.gcl_lex import gcl_lex

class TestGclLex(unittest.TestCase):

    def setUp(self):
        pass

    def test_trivial_corpus(self):
        expr = '123 ... 456'
        results = gcl_lex(expr)

        # TODO run some tests
        # self.assertEqual( result, expected )
