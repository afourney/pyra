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
        self.assertEqual( icovers._first_starting_at_or_after(0)["extent"],  (4,6) )
        self.assertEqual( icovers._first_starting_at_or_after(5)["extent"],  (INF,INF) )

        icovers = cdr.iCovers(2, ["10","20","30"])
        self.assertEqual( icovers._first_starting_at_or_after(0)["extent"],  (3,4) )
        self.assertEqual( icovers._first_starting_at_or_after(4)["extent"],  (4,5) )
        self.assertEqual( icovers._first_starting_at_or_after(5)["extent"],  (5,6) )
        self.assertEqual( icovers._first_starting_at_or_after(6)["extent"],  (6,7) )
        self.assertEqual( icovers._first_starting_at_or_after(7)["extent"],  (INF,INF) )


    def test_rank(self):
        # Both terms occur once in four tokens. The adjacent two-term cover
        # scores 2 bits, as do the singleton covers.
        ranker = CoverDensityRanking(InvertedIndex("a b x x".split()))
        results = ranker.rank(["a", "b"])
        self.assertEqual(len(results), 3)
        self.assertEqual({cover["extent"] for cover, _ in results},
                         {(0, 0), (1, 1), (0, 1)})
        for cover, score in results:
            self.assertEqual(set(cover["terms"]),
                             set("a b x x".split()[cover["extent"][0]:cover["extent"][1] + 1]))
            self.assertAlmostEqual(score, 2.0)
        self.assertEqual(ranker.rank(["a", "b", "a"]), results)
        self.assertEqual(ranker.rank([]), [])
        self.assertEqual(ranker.rank(["missing"]), [])

    def test_rank_orders_by_score(self):
        ranker = CoverDensityRanking(InvertedIndex("rare common common common".split()))
        results = ranker.rank(["rare", "common"])
        self.assertEqual(results[0][0]["extent"], (0, 0))
        self.assertAlmostEqual(results[0][1], 2.0)
        self.assertEqual([score for _, score in results],
                         sorted((score for _, score in results), reverse=True))
