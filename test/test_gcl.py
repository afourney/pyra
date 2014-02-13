# Load what we actually need to run the tests
import unittest
from pyra.iindex import InvertedIndex, INF
from pyra.gcl import GCL

class TestProcessor(unittest.TestCase):

    def setUp(self):
        pass


    def test_single_token(self):
        corpus  = "00 10 10 10 20 10 30 10 40 10 50 10 60 10 70 10 80 10 90 00"
                #   0  1  2  3  4  5  6  7  8  9 10 11 12 13 14 15 16 17 18 19
        tokens  = corpus.split()
        iidx    = InvertedIndex(tokens)
        g       = GCL(iidx)  

        query = g.parse('"30"')

        self.assertEqual( query._first_starting_at_or_after(0),  (6,6) )
        self.assertEqual( query._first_starting_at_or_after(5),  (6,6) )
        self.assertEqual( query._first_starting_at_or_after(6),  (6,6) )
        self.assertEqual( query._first_starting_at_or_after(7),  (INF,INF) )

        self.assertEqual( query._first_ending_at_or_after(0),  (6,6) )
        self.assertEqual( query._first_ending_at_or_after(5),  (6,6) )
        self.assertEqual( query._first_ending_at_or_after(6),  (6,6) )
        self.assertEqual( query._first_ending_at_or_after(7),  (INF,INF) )

        self.assertEqual( query._last_starting_at_or_before(5),  (-INF,-INF) )
        self.assertEqual( query._last_starting_at_or_before(6),  (6,6) )
        self.assertEqual( query._last_starting_at_or_before(7),  (6,6) )

        self.assertEqual( query._last_ending_at_or_before(5),  (-INF,-INF) )
        self.assertEqual( query._last_ending_at_or_before(6),  (6,6) )
        self.assertEqual( query._last_ending_at_or_before(7),  (6,6) )


    def test_single_token(self):
        corpus  = "00 10 10 10 20 10 30 10 40 10 50 10 60 10 70 10 80 10 90 00"
                #   0  1  2  3  4  5  6  7  8  9 10 11 12 13 14 15 16 17 18 19
        tokens  = corpus.split()
        iidx    = InvertedIndex(tokens)
        g       = GCL(iidx)  

        query = g.parse('"30".."50"')

        self.assertEqual( query._first_starting_at_or_after(0),  (6,10) )
        self.assertEqual( query._first_starting_at_or_after(5),  (6,10) )
        self.assertEqual( query._first_starting_at_or_after(6),  (6,10) )
        self.assertEqual( query._first_starting_at_or_after(7),  (INF,INF) )

        self.assertEqual( query._first_ending_at_or_after(0),  (6,10) )
        self.assertEqual( query._first_ending_at_or_after(5),  (6,10) )
        self.assertEqual( query._first_ending_at_or_after(6),  (6,10) )
        self.assertEqual( query._first_ending_at_or_after(7),  (6,10) )
        self.assertEqual( query._first_ending_at_or_after(10),  (6,10) )
        self.assertEqual( query._first_ending_at_or_after(11),  (INF,INF) )


    def test_containing(self):
        corpus  = "00 10 10 10 20 10 30 10 40 10 50 10 60 10 70 10 80 10 90 00"
                #   0  1  2  3  4  5  6  7  8  9 10 11 12 13 14 15 16 17 18 19
        tokens  = corpus.split()
        iidx    = InvertedIndex(tokens)
        g       = GCL(iidx)  

        outer = g.parse('"20" .. "50"') 

        self.assertEqual( g.parse('%1 > "30"', outer )._first_starting_at_or_after(0),  (4,10) )
        self.assertEqual( g.parse('%1 > "30"', outer )._first_starting_at_or_after(4),  (4,10) )
        self.assertEqual( g.parse('%1 > "30"', outer )._first_starting_at_or_after(5),  (INF,INF) )
        self.assertEqual( g.parse('%1 > "30"', outer )._first_starting_at_or_after(6),  (INF,INF) )
        self.assertEqual( g.parse('%1 > "30"', outer )._first_starting_at_or_after(10), (INF,INF) )
        self.assertEqual( g.parse('%1 > "20"', outer )._first_starting_at_or_after(0),  (4,10) )
        self.assertEqual( g.parse('%1 > "20"', outer )._first_starting_at_or_after(4),  (4,10) )
        self.assertEqual( g.parse('%1 > "20"', outer )._first_starting_at_or_after(5),  (INF,INF) )
        self.assertEqual( g.parse('%1 > "20"', outer )._first_starting_at_or_after(6),  (INF,INF) )
        self.assertEqual( g.parse('%1 > "20"', outer )._first_starting_at_or_after(10), (INF,INF) )
        self.assertEqual( g.parse('%1 > "50"', outer )._first_starting_at_or_after(0),  (4,10) )
        self.assertEqual( g.parse('%1 > "50"', outer )._first_starting_at_or_after(4),  (4,10) )
        self.assertEqual( g.parse('%1 > "50"', outer )._first_starting_at_or_after(5),  (INF,INF) )
        self.assertEqual( g.parse('%1 > "50"', outer )._first_starting_at_or_after(6),  (INF,INF) )
        self.assertEqual( g.parse('%1 > "50"', outer )._first_starting_at_or_after(10), (INF,INF) )


        self.assertEqual( g.parse('%1 > "30"', outer )._first_ending_at_or_after(0),  (4,10) )
        self.assertEqual( g.parse('%1 > "30"', outer )._first_ending_at_or_after(5),  (4,10) )
        self.assertEqual( g.parse('%1 > "30"', outer )._first_ending_at_or_after(6),  (4,10) )
        self.assertEqual( g.parse('%1 > "30"', outer )._first_ending_at_or_after(7),  (4,10) )
        self.assertEqual( g.parse('%1 > "20"', outer )._first_ending_at_or_after(0),  (4,10) )
        self.assertEqual( g.parse('%1 > "20"', outer )._first_ending_at_or_after(3),  (4,10) )
        self.assertEqual( g.parse('%1 > "20"', outer )._first_ending_at_or_after(4),  (4,10) )
        self.assertEqual( g.parse('%1 > "20"', outer )._first_ending_at_or_after(5),  (4,10) )
        self.assertEqual( g.parse('%1 > "50"', outer )._first_ending_at_or_after(0),  (4,10) )
        self.assertEqual( g.parse('%1 > "50"', outer )._first_ending_at_or_after(9),  (4,10) )
        self.assertEqual( g.parse('%1 > "50"', outer )._first_ending_at_or_after(10), (4,10) )
        self.assertEqual( g.parse('%1 > "50"', outer )._first_ending_at_or_after(11), (INF,INF) )



    def test_contained_in(self):
        corpus  = "00 10 10 10 20 10 30 10 40 10 50 10 60 10 70 10 80 10 90 00"
                #   0  1  2  3  4  5  6  7  8  9 10 11 12 13 14 15 16 17 18 19
        tokens  = corpus.split()
        iidx    = InvertedIndex(tokens)
        g       = GCL(iidx)  

        outer = g.parse('"20" .. "50"') 


        self.assertEqual( g.parse('"30" < %1', outer )._first_starting_at_or_after(0),  (6,6) )
        self.assertEqual( g.parse('"30" < %1', outer )._first_starting_at_or_after(5),  (6,6) )
        self.assertEqual( g.parse('"30" < %1', outer )._first_starting_at_or_after(6),  (6,6) )
        self.assertEqual( g.parse('"30" < %1', outer )._first_starting_at_or_after(7),  (INF,INF) )
        self.assertEqual( g.parse('"20" < %1', outer )._first_starting_at_or_after(0),  (4,4) )
        self.assertEqual( g.parse('"20" < %1', outer )._first_starting_at_or_after(3),  (4,4) )
        self.assertEqual( g.parse('"20" < %1', outer )._first_starting_at_or_after(4),  (4,4) )
        self.assertEqual( g.parse('"20" < %1', outer )._first_starting_at_or_after(5),  (INF,INF) )
        self.assertEqual( g.parse('"50" < %1', outer )._first_starting_at_or_after(0),  (10,10) )
        self.assertEqual( g.parse('"50" < %1', outer )._first_starting_at_or_after(9),  (10,10) )
        self.assertEqual( g.parse('"50" < %1', outer )._first_starting_at_or_after(10), (10,10) )
        self.assertEqual( g.parse('"50" < %1', outer )._first_starting_at_or_after(11), (INF,INF) )

        self.assertEqual( g.parse('"30" < %1', outer )._first_ending_at_or_after(0),  (6,6) )
        self.assertEqual( g.parse('"30" < %1', outer )._first_ending_at_or_after(5),  (6,6) )
        self.assertEqual( g.parse('"30" < %1', outer )._first_ending_at_or_after(6),  (6,6) )
        self.assertEqual( g.parse('"30" < %1', outer )._first_ending_at_or_after(7),  (INF,INF) )
        self.assertEqual( g.parse('"20" < %1', outer )._first_ending_at_or_after(0),  (4,4) )
        self.assertEqual( g.parse('"20" < %1', outer )._first_ending_at_or_after(3),  (4,4) )
        self.assertEqual( g.parse('"20" < %1', outer )._first_ending_at_or_after(4),  (4,4) )
        self.assertEqual( g.parse('"20" < %1', outer )._first_ending_at_or_after(5),  (INF,INF) )
        self.assertEqual( g.parse('"50" < %1', outer )._first_ending_at_or_after(0),  (10,10) )
        self.assertEqual( g.parse('"50" < %1', outer )._first_ending_at_or_after(9),  (10,10) )
        self.assertEqual( g.parse('"50" < %1', outer )._first_ending_at_or_after(10), (10,10) )
        self.assertEqual( g.parse('"50" < %1', outer )._first_ending_at_or_after(11), (INF,INF) )


    def test_trivial_corpus(self):
        corpus  = "the quick brown fox jumps over the lazy dog and the brown dog runs away"
        tokens  = corpus.split()
        iidx    = InvertedIndex(tokens)
        g       = GCL(iidx)  

        # A random spattering of tests...

        self.assertEqual(list( g.Term('dog')), [slice(8,9), slice(12,13)])
        self.assertEqual(list( g.Term('cat') ), [])
        self.assertEqual(list( g.Term('fox') ), [slice(3,4)])
        self.assertEqual(list( g.BoundedBy(g.Term('brown'), g.Term('dog')) ), [slice(2,9), slice(11,13)])
        self.assertEqual(list( g.Containing(g.BoundedBy(g.Term('brown'), g.Term('dog')), g.Term('over')) ), [slice(2,9)])
        self.assertEqual(list( g.Containing(g.BoundedBy(g.Term('brown'), g.Term('dog')), g.Term('and')) ),  [])
        self.assertEqual(list( g.ContainedIn(g.Term('over'), g.BoundedBy(g.Term('brown'), g.Term('dog'))) ), [slice(5,6)])
        self.assertEqual(list( g.Phrase('quick', 'brown', 'fox') ),     [slice(1,4)] )
        self.assertEqual(list( g.Phrase('quick', 'grey', 'fox')  ),     [] )
        self.assertEqual(list( g.Containing(g.BoundedBy(g.Term('brown'), g.Term('dog')), g.Term('and')) ),  [])
        self.assertEqual(list( g.Containing(g.BoundedBy(g.Term('brown'), g.Term('dog')), g.Slice( slice(2,3) )) ), [slice(2,9)])
        self.assertEqual(list( g.Containing(g.BoundedBy(g.Term('brown'), g.Term('dog')), g.Slice( slice(2,9) )) ), [slice(2,9)])
        self.assertEqual(list( g.Containing(g.BoundedBy(g.Term('brown'), g.Term('dog')), g.Slice( slice(6,7) )) ), [slice(2,9)])
        self.assertEqual(list( g.Containing(g.BoundedBy(g.Term('brown'), g.Term('dog')), g.Slice( slice(3,5) )) ), [slice(2,9)])
        self.assertEqual(list( g.Containing(g.BoundedBy(g.Term('brown'), g.Term('dog')), g.Slice( slice(1,5) )) ), [])
        self.assertEqual(list( g.Containing(g.BoundedBy(g.Term('brown'), g.Term('dog')), g.Slice( slice(11,12) )) ), [slice(11,13)])

        # Figure out
        #self.assertEqual(list( g.Containing(g.BoundedBy(g.Term('brown'), g.Term('dog')), g.Slice( slice(12,13) )) ), [slice(11,13)])

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
