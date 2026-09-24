# Load what we actually need to run the tests
import unittest

from pyra.icover import CoverDensityRanking
from pyra.iindex import INF, InvertedIndex


class TestICover(unittest.TestCase):
    def setUp(self):
        pass

    def test_icover(self):
        corpus = "00 10 10 10 20 10 30 10 40 10 50 10 60 10 70 10 80 10 90 00"
        #   0  1  2  3  4  5  6  7  8  9 10 11 12 13 14 15 16 17 18 19
        tokens = corpus.split()
        iidx = InvertedIndex(tokens)
        cdr = CoverDensityRanking(iidx)

        icovers = cdr.iCovers(3, ["10", "20", "30"])
        self.assertEqual(icovers._first_starting_at_or_after(0)["extent"], (4, 6))
        self.assertEqual(icovers._first_starting_at_or_after(5)["extent"], (INF, INF))

        icovers = cdr.iCovers(2, ["10", "20", "30"])
        self.assertEqual(icovers._first_starting_at_or_after(0)["extent"], (3, 4))
        self.assertEqual(icovers._first_starting_at_or_after(4)["extent"], (4, 5))
        self.assertEqual(icovers._first_starting_at_or_after(5)["extent"], (5, 6))
        self.assertEqual(icovers._first_starting_at_or_after(6)["extent"], (6, 7))
        self.assertEqual(icovers._first_starting_at_or_after(7)["extent"], (INF, INF))

    def test_rank(self):
        # Both terms occur once in four tokens. The adjacent two-term cover
        # scores 2 bits, as do the singleton covers.
        ranker = CoverDensityRanking(InvertedIndex(["a", "b", "x", "x"]))
        results = ranker.rank(["a", "b"])
        self.assertEqual(len(results), 3)
        self.assertEqual(
            {(cover["slice"].start, cover["slice"].stop) for cover, _ in results},
            {(0, 1), (1, 2), (0, 2)},
        )
        for cover, score in results:
            self.assertEqual(
                set(cover["terms"]),
                set(["a", "b", "x", "x"][cover["slice"]]),
            )
            self.assertAlmostEqual(score, 2.0)
        self.assertEqual(ranker.rank(["a", "b", "a"]), results)
        self.assertEqual(ranker.rank([]), [])
        self.assertEqual(ranker.rank(["missing"]), [])

    def test_rank_orders_by_score(self):
        ranker = CoverDensityRanking(InvertedIndex(["rare", "common", "common", "common"]))
        results = ranker.rank(["rare", "common"])
        self.assertEqual(results[0][0]["slice"], slice(0, 1))
        self.assertAlmostEqual(results[0][1], 2.0)
        self.assertEqual(
            [score for _, score in results], sorted((score for _, score in results), reverse=True)
        )

    def test_public_cover_slices(self):
        tokens = ["a", "x", "b", "a", "b"]
        ranker = CoverDensityRanking(InvertedIndex(tokens))
        covers = list(ranker.iCovers(2, ["a", "b"]))
        self.assertEqual(
            [cover["slice"] for cover in covers], [slice(0, 3), slice(2, 4), slice(3, 5)]
        )
        for cover in covers:
            self.assertEqual(set(cover), {"slice", "terms"})
            self.assertEqual(set(cover["terms"]), {"a", "b"})
            self.assertIsInstance(cover["slice"].start, int)
            self.assertIsInstance(cover["slice"].stop, int)
        self.assertEqual(tokens[covers[-1]["slice"]], ["a", "b"])
        self.assertEqual(list(ranker.iCovers(2, ["a", "missing"])), [])
        self.assertEqual(list(ranker.iCovers(2, ["a", "b"]).iterator(3)), covers[2:])
        self.assertEqual(list(ranker.iCovers(2, ["a", "b"]).iterator(5)), [])

    def test_singleton_and_empty_corpus(self):
        ranker = CoverDensityRanking(InvertedIndex(["only"]))
        self.assertEqual(ranker.rank(["only"]), [({"slice": slice(0, 1), "terms": ["only"]}, 0.0)])
        self.assertEqual(CoverDensityRanking(InvertedIndex([])).rank(["only"]), [])
