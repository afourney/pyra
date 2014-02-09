# Load what we actually need to run the tests
import unittest
from pyra.iindex import InvertedIndex, INF
from pyra.gcl import GCL

class TestProcessor(unittest.TestCase):

    def setUp(self):
        pass

    def test_trivial_corpus(self):
        corpus  = "the quick brown fox jumps over the lazy dog and the brown dog runs away"
        tokens  = corpus.split()
        iidx    = InvertedIndex(tokens)
        g       = GCL(iidx)  

        self.assertEqual([ t for t in g.Term('dog') ], [slice(8,9), slice(12,13)])
        self.assertEqual([ t for t in g.Term('cat') ], [])
        self.assertEqual([ t for t in g.Term('fox') ], [slice(3,4)])
        self.assertEqual([ t for t in g.BoundedBy(g.Term('brown'), g.Term('dog')) ], [slice(2,9), slice(11,13)])
        self.assertEqual([ t for t in g.Containing(g.BoundedBy(g.Term('brown'), g.Term('dog')), g.Term('over')) ], [slice(2,9)])
        self.assertEqual([ t for t in g.Containing(g.BoundedBy(g.Term('brown'), g.Term('dog')), g.Term('and')) ],  [])
        self.assertEqual([ t for t in g.Phrase('quick', 'brown', 'fox') ],     [slice(1,4)] )
        self.assertEqual([ t for r in g.Phrase('quick', 'grey', 'fox')  ],     [] )
        self.assertEqual([ t for t in g.Containing(g.BoundedBy(g.Term('brown'), g.Term('dog')), g.Term('and')) ],  [])
        self.assertEqual([ t for t in g.Containing(g.BoundedBy(g.Term('brown'), g.Term('dog')), g.Extent( (2,2) )) ], [slice(2,9)])
        self.assertEqual([ t for t in g.Containing(g.BoundedBy(g.Term('brown'), g.Term('dog')), g.Extent( (2,8) )) ], [slice(2,9)])
        self.assertEqual([ t for t in g.Containing(g.BoundedBy(g.Term('brown'), g.Term('dog')), g.Extent( (6,6) )) ], [slice(2,9)])
        self.assertEqual([ t for t in g.Containing(g.BoundedBy(g.Term('brown'), g.Term('dog')), g.Extent( (3,4) )) ], [slice(2,9)])
        self.assertEqual([ t for t in g.Containing(g.BoundedBy(g.Term('brown'), g.Term('dog')), g.Extent( (1,4) )) ], [])
        self.assertEqual([ t for t in g.Containing(g.BoundedBy(g.Term('brown'), g.Term('dog')), g.Extent( (11,11) )) ], [slice(11,13)])
        self.assertEqual([ t for t in g.Containing(g.BoundedBy(g.Term('brown'), g.Term('dog')), g.Extent( (12,12) )) ], [slice(11,13)])
        self.assertEqual([ t for t in g.Containing(g.List( (1,13), (10,14), (14,16) ), g.Extent( (12,12) )) ], [slice(1,14), slice(10,15)] )
        self.assertEqual([ t for t in g.Containing(g.List( (5,13), (10,14), (14,16) ), g.Extent( (2,2) )) ], [] )
