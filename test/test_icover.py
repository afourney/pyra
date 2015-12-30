# Load what we actually need to run the tests
import unittest
from pyra.iindex import InvertedIndex, INF
from pyra.icover import CoverDensityRanking

class TestICover(unittest.TestCase):

    def setUp(self):
        pass


    def test_icover(self):
        corpus  = "00 10 10 10 20 10 30 10 40 10 50 10 60 10 70 10 80 10 90 00"
                #   0  1  2  3  4  5  6  7  8  9 10 11 12 13 14 15 16 17 18 19
        tokens  = corpus.split()
        iidx    = InvertedIndex(tokens)
        cdr     = CoverDensityRanking(iidx)  

        icovers = cdr.iCovers(3, ["10","20","30"])
        self.assertEqual( icovers._first_starting_at_or_after(0),  (4,6) )
        self.assertEqual( icovers._first_starting_at_or_after(5),  (INF,INF) )

        icovers = cdr.iCovers(2, ["10","20","30"])
        self.assertEqual( icovers._first_starting_at_or_after(0),  (3,4) )
        self.assertEqual( icovers._first_starting_at_or_after(4),  (4,5) )
        self.assertEqual( icovers._first_starting_at_or_after(5),  (5,6) )
        self.assertEqual( icovers._first_starting_at_or_after(6),  (6,7) )
        self.assertEqual( icovers._first_starting_at_or_after(7),  (INF,INF) )

