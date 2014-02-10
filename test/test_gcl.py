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

        self.assertEqual(list( g.Term('dog')), [slice(8,9), slice(12,13)])
        self.assertEqual(list( g.Term('cat') ), [])
        self.assertEqual(list( g.Term('fox') ), [slice(3,4)])
        self.assertEqual(list( g.BoundedBy(g.Term('brown'), g.Term('dog')) ), [slice(2,9), slice(11,13)])
        self.assertEqual(list( g.Containing(g.BoundedBy(g.Term('brown'), g.Term('dog')), g.Term('over')) ), [slice(2,9)])
        self.assertEqual(list( g.Containing(g.BoundedBy(g.Term('brown'), g.Term('dog')), g.Term('and')) ),  [])
        self.assertEqual(list( g.Phrase('quick', 'brown', 'fox') ),     [slice(1,4)] )
        self.assertEqual(list( g.Phrase('quick', 'grey', 'fox')  ),     [] )
        self.assertEqual(list( g.Containing(g.BoundedBy(g.Term('brown'), g.Term('dog')), g.Term('and')) ),  [])
        self.assertEqual(list( g.Containing(g.BoundedBy(g.Term('brown'), g.Term('dog')), g.Slice( slice(2,3) )) ), [slice(2,9)])
        self.assertEqual(list( g.Containing(g.BoundedBy(g.Term('brown'), g.Term('dog')), g.Slice( slice(2,9) )) ), [slice(2,9)])
        self.assertEqual(list( g.Containing(g.BoundedBy(g.Term('brown'), g.Term('dog')), g.Slice( slice(6,7) )) ), [slice(2,9)])
        self.assertEqual(list( g.Containing(g.BoundedBy(g.Term('brown'), g.Term('dog')), g.Slice( slice(3,5) )) ), [slice(2,9)])
        self.assertEqual(list( g.Containing(g.BoundedBy(g.Term('brown'), g.Term('dog')), g.Slice( slice(1,5) )) ), [])
        self.assertEqual(list( g.Containing(g.BoundedBy(g.Term('brown'), g.Term('dog')), g.Slice( slice(11,12) )) ), [slice(11,13)])
        self.assertEqual(list( g.Containing(g.BoundedBy(g.Term('brown'), g.Term('dog')), g.Slice( slice(12,13) )) ), [slice(11,13)])

        # Remember, slice ends are open and do not include the end idx
        self.assertEqual(list( g.Length(1) ), [ slice(i, i+1) for i in range(0, len(tokens)) ])
        self.assertEqual(list( g.Length(4) ), [ slice(i, i+4) for i in range(0, len(tokens)-3) ])
        self.assertEqual(list( g.Length(len(tokens)) ), [ slice(0, len(tokens)) ])
        self.assertEqual(list( g.Length(len(tokens) + 1) ), [])
        self.assertEqual(list( g.Length(1).iterator(reverse=True) ), [ slice(i, i+1) for i in range(len(tokens)-1,-1,-1) ])
        self.assertEqual(list( g.Length(4).iterator(reverse=True) ), [ slice(i, i+4) for i in range(len(tokens)-4,-1,-1) ])
        self.assertEqual(list( g.Length(len(tokens)).iterator(reverse=True) ), [ slice(0, len(tokens)) ])
        self.assertEqual(list( g.Length(len(tokens) + 1).iterator(reverse=True) ), [])

        self.assertEqual(list( g.Start(g.Term('fox')) ), [slice(3,4)])
        self.assertEqual(list( g.End(g.Term('fox')) ), [slice(3,4)])
        
        self.assertEqual(list( g.Start(g.Phrase('quick', 'brown', 'fox') )),     [slice(1,2)] )
        self.assertEqual(list( g.End(g.Phrase('quick', 'brown', 'fox') )),     [slice(3,4)] )
        
        self.assertEqual(list( g.Start(g.Length(1)) ), [ slice(i, i+1) for i in range(0, len(tokens)) ])
        self.assertEqual(list( g.Start(g.Length(4)) ), [ slice(i, i+1) for i in range(0, len(tokens)-3) ])
        self.assertEqual(list( g.Start(g.Length(1)).iterator(reverse=True) ), [ slice(i, i+1) for i in range(len(tokens)-1,-1,-1) ])
        self.assertEqual(list( g.Start(g.Length(4)).iterator(reverse=True) ), [ slice(i, i+1) for i in range(len(tokens)-4,-1,-1) ])

        self.assertEqual(list( g.End(g.Length(1)) ), [ slice(i, i+1) for i in range(0, len(tokens)) ])
        self.assertEqual(list( g.End(g.Length(4)) ), [ slice(i+3, i+4) for i in range(0, len(tokens)-3) ])
        self.assertEqual(list( g.End(g.Length(1)).iterator(reverse=True) ), [ slice(i, i+1) for i in range(len(tokens)-1,-1,-1) ])
        self.assertEqual(list( g.End(g.Length(4)).iterator(reverse=True) ), [ slice(i+3, i+4) for i in range(len(tokens)-4,-1,-1) ])
