# Load what we actually need to run the tests
import unittest
from pyra.gcl_yacc import gcl_yacc_parse

class TestGclLex(unittest.TestCase):

    def setUp(self):
        pass

    def test_trivial_corpus(self):
        expr = '123 .. 456 > "hello"'
        results = gcl_yacc_parse(expr)

        self.assertEqual(results, (
            'Containing',
            ('BoundedBy', ('Position', 123), ('Position', 456)),
            ('Phrase', 'hello'),
        ))
