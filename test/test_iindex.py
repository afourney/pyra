# Load what we actually need to run the tests
import unittest
from pyra.iindex import InvertedIndex, INF

class TestInvertedIndex(unittest.TestCase):

    def setUp(self):
        pass

    def test_trivial_corpus(self):
        corpus = "the quick brown fox jumps over the lazy dog and the brown dog runs away"
        tokens = corpus.split()
        iidx   = InvertedIndex(tokens)

        self.assertEqual(iidx.corpus_length,                                15)
        self.assertEqual(iidx.first('dog'),                                 8)
        self.assertEqual(iidx.last('dog'),                                  12)
        self.assertEqual(iidx.next('dog', 8),                               12)
        self.assertEqual(iidx.prev('dog', 12),                              8)
        self.assertEqual(iidx.first('cat'),                                 INF)
        self.assertEqual(iidx.last('cat'),                                 -INF)
        self.assertEqual(iidx.next('cat', 8),                               INF)
        self.assertEqual(iidx.prev('cat', 12),                             -INF)
        self.assertEqual(iidx.first('fox'),                                 3)
        self.assertEqual(iidx.last('fox'),                                  3)
        self.assertEqual(iidx.frequency('dog', -INF, INF),             2)
        self.assertEqual(iidx.frequency('dog', -INF, 10),              1)
        self.assertEqual(iidx.frequency('dog', -INF, 9),               1)
        self.assertEqual(iidx.frequency('dog', -INF, 8),               0)
        self.assertEqual(iidx.frequency('dog', 7, 14),                 2)
        self.assertEqual(iidx.frequency('dog', 8, 13),                 2)
        self.assertEqual(iidx.frequency('dog', 12, INF),               1)
        self.assertEqual(iidx.frequency('dog', 13, 15),                0)
        self.assertEqual(iidx.frequency('dog', slice(None,None)),      2)
        self.assertEqual(iidx.frequency('dog', slice(None,10)),        1)
        self.assertEqual(iidx.frequency('dog', slice(None,9)),         1)
        self.assertEqual(iidx.frequency('dog', slice(None,8)),         0)
        self.assertEqual(iidx.frequency('dog', slice(7, 14)),          2)
        self.assertEqual(iidx.frequency('dog', slice(8, 13)),          2)
        self.assertEqual(iidx.frequency('dog', slice(12)),             1)
        self.assertEqual(iidx.frequency('dog', slice(13, 15)),         0)
 
        self.assertEqual(iidx.frequency('cat', -INF, INF),             0)
        self.assertEqual(iidx.frequency('cat', 2, INF),                0)
        self.assertEqual(iidx.frequency('cat', -INF, 4),               0)
        self.assertEqual(iidx.frequency('cat', 2, 5),                  0)
        self.assertEqual(list(iidx.postings('dog')),                   [8, 12])
        self.assertEqual(list(iidx.postings('dog', reverse=True)),     [12,8])
        self.assertEqual(list(iidx.postings('dog', 12)),               [12])
        self.assertEqual(list(iidx.postings('cat')),                   [])
        self.assertEqual(list(iidx.postings('cat', reverse=True)),     [])
        self.assertEqual(iidx.dictionary() ^ set(tokens),                   set())
