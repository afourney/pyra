# Load what we actually need to run the tests
import unittest
from pyra.iindex import InvertedIndex, INF
from pyra.processor import QueryProcessor
from pyra.operators import *

class TestProcessor(unittest.TestCase):

    def setUp(self):
        pass

    def test_trivial_corpus(self):
        corpus = "the quick brown fox jumps over the lazy dog and the brown dog runs away"
        tokens = corpus.split()
        iidx   = InvertedIndex(tokens)
        qproc  = QueryProcessor(iidx)

        self.assertEqual(qproc.list( Term('dog') ), [slice(8,9), slice(12,13)])
        self.assertEqual(qproc.list( Term('cat') ), [])
        self.assertEqual(qproc.list( Term('fox') ), [slice(3,4)])
        self.assertEqual(qproc.list( Bounded(Term('brown'), Term('dog')) ), [slice(2,9), slice(11,13)])
        self.assertEqual(qproc.list( Containing(Bounded(Term('brown'), Term('dog')), Term('over')) ), [slice(2,9)])
        self.assertEqual(qproc.list( Containing(Bounded(Term('brown'), Term('dog')), Term('and')) ),  [])
        self.assertEqual(qproc.list( Containing(Bounded(Term('brown'), Term('dog')), Extent( (2,2) )) ), [slice(2,9)])
        self.assertEqual(qproc.list( Containing(Bounded(Term('brown'), Term('dog')), Extent( (2,8) )) ), [slice(2,9)])
        self.assertEqual(qproc.list( Containing(Bounded(Term('brown'), Term('dog')), Extent( (6,6) )) ), [slice(2,9)])
        self.assertEqual(qproc.list( Containing(Bounded(Term('brown'), Term('dog')), Extent( (3,4) )) ), [slice(2,9)])
        self.assertEqual(qproc.list( Containing(Bounded(Term('brown'), Term('dog')), Extent( (1,4) )) ), [])
        self.assertEqual(qproc.list( Containing(Bounded(Term('brown'), Term('dog')), Extent( (11,11) )) ), [slice(11,13)])
        self.assertEqual(qproc.list( Containing(Bounded(Term('brown'), Term('dog')), Extent( (12,12) )) ), [slice(11,13)])
        self.assertEqual(qproc.list( Phrase('quick', 'brown', 'fox')),     [slice(1,4)] )
        self.assertEqual(qproc.list( Phrase('quick', 'grey', 'fox')),      [] )
        self.assertEqual(qproc.list( Containing(GCList( (1,13), (10,14), (14,16) ), Extent( (12,12) )) ), [slice(1,14), slice(10,15)] )
        self.assertEqual(qproc.list( Containing(GCList( (5,13), (10,14), (14,16) ), Extent( (2,2) )) ), [] )
