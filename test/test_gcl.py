# Load what we actually need to run the tests
import unittest
from itertools import combinations

from pyra.gcl import GCL, ListGenerator
from pyra.iindex import INF, InvertedIndex


class TestProcessor(unittest.TestCase):
    def setUp(self):
        pass

    def test_single_token(self):
        corpus = "00 10 10 10 20 10 30 10 40 10 50 10 60 10 70 10 80 10 90 00"
        #   0  1  2  3  4  5  6  7  8  9 10 11 12 13 14 15 16 17 18 19
        tokens = corpus.split()
        iidx = InvertedIndex(tokens)
        g = GCL(iidx)

        query = g.parse('"30"')

        self.assertEqual(query._first_starting_at_or_after(0), (6, 6))
        self.assertEqual(query._first_starting_at_or_after(5), (6, 6))
        self.assertEqual(query._first_starting_at_or_after(6), (6, 6))
        self.assertEqual(query._first_starting_at_or_after(7), (INF, INF))

        self.assertEqual(query._first_ending_at_or_after(0), (6, 6))
        self.assertEqual(query._first_ending_at_or_after(5), (6, 6))
        self.assertEqual(query._first_ending_at_or_after(6), (6, 6))
        self.assertEqual(query._first_ending_at_or_after(7), (INF, INF))

        self.assertEqual(query._last_starting_at_or_before(5), (-INF, -INF))
        self.assertEqual(query._last_starting_at_or_before(6), (6, 6))
        self.assertEqual(query._last_starting_at_or_before(7), (6, 6))

        self.assertEqual(query._last_ending_at_or_before(5), (-INF, -INF))
        self.assertEqual(query._last_ending_at_or_before(6), (6, 6))
        self.assertEqual(query._last_ending_at_or_before(7), (6, 6))

    def test_bounded_by(self):
        corpus = "00 10 10 10 20 10 30 10 40 10 50 10 60 10 70 10 80 10 90 00"
        #   0  1  2  3  4  5  6  7  8  9 10 11 12 13 14 15 16 17 18 19
        tokens = corpus.split()
        iidx = InvertedIndex(tokens)
        g = GCL(iidx)

        query = g.parse('"30".."50"')

        self.assertEqual(query._first_starting_at_or_after(0), (6, 10))
        self.assertEqual(query._first_starting_at_or_after(5), (6, 10))
        self.assertEqual(query._first_starting_at_or_after(6), (6, 10))
        self.assertEqual(query._first_starting_at_or_after(7), (INF, INF))

        self.assertEqual(query._first_ending_at_or_after(0), (6, 10))
        self.assertEqual(query._first_ending_at_or_after(5), (6, 10))
        self.assertEqual(query._first_ending_at_or_after(6), (6, 10))
        self.assertEqual(query._first_ending_at_or_after(7), (6, 10))
        self.assertEqual(query._first_ending_at_or_after(10), (6, 10))
        self.assertEqual(query._first_ending_at_or_after(11), (INF, INF))

    def test_unicode_phrase(self):
        tokens = ["caf\u00e9", "\u8336", "caf\u00e9", "\u8336"]
        g = GCL(InvertedIndex(tokens))
        query = g.parse('"caf\u00e9", "\u8336"')
        self.assertEqual(list(query), [slice(0, 2), slice(2, 4)])

    def _assert_access_functions(self, query, extents):
        positions = [-INF, *list(range(-1, query.inverted_index.corpus_length + 1)), INF]
        for k in positions + positions[::-1]:
            starting_after = [(u, v) for u, v in extents if u >= k]
            ending_after = [(u, v) for u, v in extents if v >= k]
            ending_before = [(u, v) for u, v in extents if v <= k]
            starting_before = [(u, v) for u, v in extents if u <= k]

            self.assertEqual(
                query._first_starting_at_or_after(k),
                starting_after[0] if starting_after else (INF, INF),
            )
            self.assertEqual(
                query._first_ending_at_or_after(k), ending_after[0] if ending_after else (INF, INF)
            )
            self.assertEqual(
                query._last_ending_at_or_before(k),
                ending_before[-1] if ending_before else (-INF, -INF),
            )
            self.assertEqual(
                query._last_starting_at_or_before(k),
                starting_before[-1] if starting_before else (-INF, -INF),
            )

        self.assertEqual(list(query), [slice(u, v + 1) for u, v in extents])
        self.assertEqual(
            list(query.iterator(reverse=True)), [slice(u, v + 1) for u, v in extents[::-1]]
        )

    def test_and_access_functions(self):
        iidx = InvertedIndex(range(16))
        g = GCL(iidx)
        a = ListGenerator(iidx, (0, 3), (5, 8), (10, 13))
        b = ListGenerator(iidx, (2, 5), (7, 10), (12, 15))

        self._assert_access_functions(g.And(a, b), [(0, 5), (2, 8), (5, 10), (7, 13), (10, 15)])
        self._assert_access_functions(g.And(b, a), [(0, 5), (2, 8), (5, 10), (7, 13), (10, 15)])
        self._assert_access_functions(g.And(a, a), [(0, 3), (5, 8), (10, 13)])

    def test_or_access_functions(self):
        iidx = InvertedIndex(range(16))
        g = GCL(iidx)
        a = ListGenerator(iidx, (0, 3), (5, 8), (10, 13))
        b = ListGenerator(iidx, (1, 3), (5, 7), (12, 15))

        self._assert_access_functions(g.Or(a, b), [(1, 3), (5, 7), (10, 13), (12, 15)])
        self._assert_access_functions(g.Or(b, a), [(1, 3), (5, 7), (10, 13), (12, 15)])
        self._assert_access_functions(g.Or(a, a), [(0, 3), (5, 8), (10, 13)])
        self._assert_access_functions(g.Or(g.Slice(slice(0, 16)), g.Position(5)), [(5, 5)])

    def test_bounded_by_access_functions(self):
        iidx = InvertedIndex(range(16))
        g = GCL(iidx)
        a = ListGenerator(iidx, (0, 3), (5, 8), (10, 13))
        b = ListGenerator(iidx, (2, 5), (7, 10), (12, 15))

        self._assert_access_functions(g.BoundedBy(a, b), [(0, 10), (5, 15)])
        self._assert_access_functions(g.BoundedBy(b, a), [(2, 13)])
        self._assert_access_functions(g.BoundedBy(a, a), [(0, 8), (5, 13)])
        self._assert_access_functions(g.BoundedBy(g.Position(0), g.Position(0)), [])
        self._assert_access_functions(g.BoundedBy(g.Position(0), g.Position(1)), [(0, 1)])

    def test_containing_access_functions(self):
        iidx = InvertedIndex(range(16))
        g = GCL(iidx)
        a = ListGenerator(iidx, (0, 3), (5, 8), (10, 13))
        b = ListGenerator(iidx, (3, 3), (8, 10))

        self._assert_access_functions(g.Containing(a, b), [(0, 3)])
        self._assert_access_functions(g.Containing(b, a), [])
        self._assert_access_functions(g.Containing(a, a), [(0, 3), (5, 8), (10, 13)])
        self._assert_access_functions(g.Containing(a, g.Position(5)), [(5, 8)])
        self._assert_access_functions(g.Containing(a, g.Position(8)), [(5, 8)])

    def test_contained_in_access_functions(self):
        iidx = InvertedIndex(range(16))
        g = GCL(iidx)
        a = ListGenerator(iidx, (0, 3), (5, 8), (10, 13))
        b = ListGenerator(iidx, (3, 3), (8, 10))

        self._assert_access_functions(g.ContainedIn(b, a), [(3, 3)])
        self._assert_access_functions(g.ContainedIn(a, b), [])
        self._assert_access_functions(g.ContainedIn(a, a), [(0, 3), (5, 8), (10, 13)])
        self._assert_access_functions(g.ContainedIn(g.Position(5), a), [(5, 5)])
        self._assert_access_functions(g.ContainedIn(g.Position(8), a), [(8, 8)])

    def test_not_containing_access_functions(self):
        iidx = InvertedIndex(range(16))
        g = GCL(iidx)
        a = ListGenerator(iidx, (0, 3), (5, 8), (10, 13))
        b = ListGenerator(iidx, (3, 3), (8, 10))

        self._assert_access_functions(g.NotContaining(a, b), [(5, 8), (10, 13)])
        self._assert_access_functions(g.NotContaining(b, a), [(3, 3), (8, 10)])
        self._assert_access_functions(g.NotContaining(a, a), [])
        self._assert_access_functions(g.NotContaining(a, g.Position(5)), [(0, 3), (10, 13)])
        self._assert_access_functions(g.NotContaining(a, g.Position(8)), [(0, 3), (10, 13)])

        a = ListGenerator(iidx, *[(i, i + 5) for i in range(8)])
        self._assert_access_functions(
            g.NotContaining(a, g.Position(4)), [(5, 10), (6, 11), (7, 12)]
        )

    def test_not_contained_in_access_functions(self):
        iidx = InvertedIndex(range(16))
        g = GCL(iidx)
        a = ListGenerator(iidx, (0, 3), (5, 8), (10, 13))
        b = ListGenerator(iidx, (3, 3), (8, 10))

        self._assert_access_functions(g.NotContainedIn(b, a), [(8, 10)])
        self._assert_access_functions(g.NotContainedIn(a, b), [(0, 3), (5, 8), (10, 13)])
        self._assert_access_functions(g.NotContainedIn(a, a), [])
        self._assert_access_functions(g.NotContainedIn(g.Position(5), a), [])
        self._assert_access_functions(g.NotContainedIn(g.Position(8), a), [])

        self._assert_access_functions(
            g.NotContainedIn(g.Length(1), g.Slice(slice(4, 12))),
            [(0, 0), (1, 1), (2, 2), (3, 3), (12, 12), (13, 13), (14, 14), (15, 15)],
        )

    def test_negative_containment_queries(self):
        corpus = "<scene> <title> hamlet </title> hamlet </scene> <scene> ghost </scene>"
        iidx = InvertedIndex(corpus.split())
        g = GCL(iidx)

        self._assert_access_functions(g.parse('("<scene>".."</scene>") /> "hamlet"'), [(6, 8)])
        self._assert_access_functions(g.parse('"hamlet" /< ("<title>".."</title>")'), [(4, 4)])
        self._assert_access_functions(
            g.parse('("<scene>".."</scene>") /> ("hamlet" + "ghost")'), []
        )
        self._assert_access_functions(g.parse('"hamlet" /< ("<scene>".."</scene>")'), [])

    def test_negative_containment_reference(self):
        iidx = InvertedIndex(range(3))
        g = GCL(iidx)
        lists = []
        for n in range(4):
            for starts in combinations(range(3), n):
                for ends in combinations(range(3), n):
                    extents = list(zip(starts, ends, strict=True))
                    if all(u <= v for u, v in extents):
                        lists.append(extents)

        for a in lists:
            for b in lists:
                ga = ListGenerator(iidx, *a)
                gb = ListGenerator(iidx, *b)
                not_containing = [(u, v) for u, v in a if not any(u <= p and q <= v for p, q in b)]
                not_contained_in = [
                    (u, v) for u, v in a if not any(p <= u and v <= q for p, q in b)
                ]
                self._assert_access_functions(g.NotContaining(ga, gb), not_containing)
                self._assert_access_functions(g.NotContainedIn(ga, gb), not_contained_in)

    def test_empty_operands(self):
        iidx = InvertedIndex(range(16))
        g = GCL(iidx)
        a = ListGenerator(iidx, (0, 3), (5, 8), (10, 13))
        b = ListGenerator(iidx)

        for operator in (g.And, g.BoundedBy, g.Containing, g.ContainedIn):
            self._assert_access_functions(operator(a, b), [])
            self._assert_access_functions(operator(b, a), [])
            self._assert_access_functions(operator(b, b), [])

        self._assert_access_functions(g.Or(a, b), [(0, 3), (5, 8), (10, 13)])
        self._assert_access_functions(g.Or(b, a), [(0, 3), (5, 8), (10, 13)])
        self._assert_access_functions(g.Or(b, b), [])

        for operator in (g.NotContaining, g.NotContainedIn):
            self._assert_access_functions(operator(a, b), [(0, 3), (5, 8), (10, 13)])
            self._assert_access_functions(operator(b, a), [])
            self._assert_access_functions(operator(b, b), [])

        g = GCL(InvertedIndex([]))
        for operator in (
            g.And,
            g.Or,
            g.BoundedBy,
            g.Containing,
            g.ContainedIn,
            g.NotContaining,
            g.NotContainedIn,
        ):
            self._assert_access_functions(operator(g.Term("a"), g.Term("b")), [])

    def test_phrase_access_functions(self):
        corpus = "a b a b x a x b a b"
        iidx = InvertedIndex(corpus.split())
        g = GCL(iidx)

        self._assert_access_functions(g.Phrase("a", "b"), [(0, 1), (2, 3), (8, 9)])
        self._assert_access_functions(g.Phrase("b", "a"), [(1, 2), (7, 8)])
        self._assert_access_functions(g.Phrase("a", "a"), [])
        self._assert_access_functions(g.And(g.Phrase("a", "b"), g.Term("x")), [(2, 4), (6, 9)])

    def test_composed_access_functions(self):
        iidx = InvertedIndex(range(16))
        g = GCL(iidx)
        a = ListGenerator(iidx, (0, 3), (5, 8), (10, 13))
        b = ListGenerator(iidx, (2, 5), (7, 10), (12, 15))

        queries = [
            (g.And(a, b), [(0, 5), (2, 8), (5, 10), (7, 13), (10, 15)]),
            (g.Or(a, b), [(0, 3), (2, 5), (5, 8), (7, 10), (10, 13), (12, 15)]),
            (g.BoundedBy(a, b), [(0, 10), (5, 15)]),
            (g.Containing(a, g.Position(7)), [(5, 8)]),
            (g.ContainedIn(a, g.Slice(slice(4, 16))), [(5, 8), (10, 13)]),
            (g.Containing(a, g.Position(15)), []),
            (g.NotContaining(a, g.Position(7)), [(0, 3), (10, 13)]),
            (g.NotContainedIn(a, g.Slice(slice(4, 16))), [(0, 3)]),
        ]

        for query, extents in queries:
            self._assert_access_functions(g.Start(query), [(u, u) for u, v in extents])
            self._assert_access_functions(g.End(query), [(v, v) for u, v in extents])
            self._assert_access_functions(g.And(query, query), extents)
            self._assert_access_functions(g.Or(query, query), extents)
            self._assert_access_functions(g.Containing(query, query), extents)
            self._assert_access_functions(g.ContainedIn(query, query), extents)
            self._assert_access_functions(g.NotContaining(query, query), [])
            self._assert_access_functions(g.NotContainedIn(query, query), [])

        query = g.parse("(%1 > 7) ^ (%2 < [4])", a, b)
        self._assert_access_functions(query, [(2, 8), (5, 10)])

        query = g.parse("(%1 /> 7) .. (%2 /< (5 .. 15))", a, b)
        self._assert_access_functions(query, [])
        query = g.parse("(%1 /> 7) ^ (%2 /< (5 .. 15))", a, b)
        self._assert_access_functions(query, [(0, 5), (2, 13)])

    def test_lazy_access_functions(self):
        class SeekOnlyGenerator(ListGenerator):
            def iterator(self, k=None, **args):
                raise AssertionError("Operands must be accessed by seeking, not iteration.")

        iidx = InvertedIndex(range(16))
        g = GCL(iidx)
        a = SeekOnlyGenerator(iidx, (0, 3), (5, 8), (10, 13))
        b = SeekOnlyGenerator(iidx, (2, 5), (7, 10), (12, 15))

        self._assert_access_functions(
            g.And(g.Containing(a, a), g.ContainedIn(b, b)),
            [(0, 5), (2, 8), (5, 10), (7, 13), (10, 15)],
        )
        self._assert_access_functions(g.BoundedBy(g.Or(a, a), g.Or(b, b)), [(0, 10), (5, 15)])
        self._assert_access_functions(
            g.Containing(g.And(a, b), g.Or(a, b)), [(0, 5), (2, 8), (5, 10), (7, 13), (10, 15)]
        )
        self._assert_access_functions(
            g.ContainedIn(g.Or(a, b), g.And(a, b)),
            [(0, 3), (2, 5), (5, 8), (7, 10), (10, 13), (12, 15)],
        )
        self._assert_access_functions(
            g.NotContaining(a, g.NotContainedIn(b, a)), [(0, 3), (5, 8), (10, 13)]
        )
        self._assert_access_functions(
            g.NotContainedIn(b, g.NotContaining(a, b)), [(2, 5), (7, 10), (12, 15)]
        )

    def test_containment_many_candidates(self):
        iidx = InvertedIndex(range(4002))
        g = GCL(iidx)
        a = ListGenerator(iidx, *[(i, i + 2) for i in range(0, 4000, 2)])
        b = ListGenerator(iidx, *[(i, i + 2) for i in range(1, 4001, 2)])

        for query in (g.Containing(a, b), g.ContainedIn(a, b)):
            self.assertEqual(query._first_starting_at_or_after(0), (INF, INF))
            self.assertEqual(query._first_ending_at_or_after(0), (INF, INF))
            self.assertEqual(query._last_ending_at_or_before(4001), (-INF, -INF))
            self.assertEqual(query._last_starting_at_or_before(4001), (-INF, -INF))

        for query in (g.NotContaining(a, a), g.NotContainedIn(a, a)):
            self.assertEqual(query._first_starting_at_or_after(0), (INF, INF))
            self.assertEqual(query._first_ending_at_or_after(0), (INF, INF))
            self.assertEqual(query._last_ending_at_or_before(4001), (-INF, -INF))
            self.assertEqual(query._last_starting_at_or_before(4001), (-INF, -INF))

    def test_containing(self):
        corpus = "00 10 10 10 20 10 30 10 40 10 50 10 60 10 70 10 80 10 90 00"
        #   0  1  2  3  4  5  6  7  8  9 10 11 12 13 14 15 16 17 18 19
        tokens = corpus.split()
        iidx = InvertedIndex(tokens)
        g = GCL(iidx)

        outer = g.parse('"20" .. "50"')

        self.assertEqual(g.parse('%1 > "30"', outer)._first_starting_at_or_after(0), (4, 10))
        self.assertEqual(g.parse('%1 > "30"', outer)._first_starting_at_or_after(4), (4, 10))
        self.assertEqual(g.parse('%1 > "30"', outer)._first_starting_at_or_after(5), (INF, INF))
        self.assertEqual(g.parse('%1 > "30"', outer)._first_starting_at_or_after(6), (INF, INF))
        self.assertEqual(g.parse('%1 > "30"', outer)._first_starting_at_or_after(10), (INF, INF))
        self.assertEqual(g.parse('%1 > "20"', outer)._first_starting_at_or_after(0), (4, 10))
        self.assertEqual(g.parse('%1 > "20"', outer)._first_starting_at_or_after(4), (4, 10))
        self.assertEqual(g.parse('%1 > "20"', outer)._first_starting_at_or_after(5), (INF, INF))
        self.assertEqual(g.parse('%1 > "20"', outer)._first_starting_at_or_after(6), (INF, INF))
        self.assertEqual(g.parse('%1 > "20"', outer)._first_starting_at_or_after(10), (INF, INF))
        self.assertEqual(g.parse('%1 > "50"', outer)._first_starting_at_or_after(0), (4, 10))
        self.assertEqual(g.parse('%1 > "50"', outer)._first_starting_at_or_after(4), (4, 10))
        self.assertEqual(g.parse('%1 > "50"', outer)._first_starting_at_or_after(5), (INF, INF))
        self.assertEqual(g.parse('%1 > "50"', outer)._first_starting_at_or_after(6), (INF, INF))
        self.assertEqual(g.parse('%1 > "50"', outer)._first_starting_at_or_after(10), (INF, INF))

        self.assertEqual(g.parse('%1 > "30"', outer)._first_ending_at_or_after(0), (4, 10))
        self.assertEqual(g.parse('%1 > "30"', outer)._first_ending_at_or_after(5), (4, 10))
        self.assertEqual(g.parse('%1 > "30"', outer)._first_ending_at_or_after(6), (4, 10))
        self.assertEqual(g.parse('%1 > "30"', outer)._first_ending_at_or_after(7), (4, 10))
        self.assertEqual(g.parse('%1 > "20"', outer)._first_ending_at_or_after(0), (4, 10))
        self.assertEqual(g.parse('%1 > "20"', outer)._first_ending_at_or_after(3), (4, 10))
        self.assertEqual(g.parse('%1 > "20"', outer)._first_ending_at_or_after(4), (4, 10))
        self.assertEqual(g.parse('%1 > "20"', outer)._first_ending_at_or_after(5), (4, 10))
        self.assertEqual(g.parse('%1 > "50"', outer)._first_ending_at_or_after(0), (4, 10))
        self.assertEqual(g.parse('%1 > "50"', outer)._first_ending_at_or_after(9), (4, 10))
        self.assertEqual(g.parse('%1 > "50"', outer)._first_ending_at_or_after(10), (4, 10))
        self.assertEqual(g.parse('%1 > "50"', outer)._first_ending_at_or_after(11), (INF, INF))

    def test_contained_in(self):
        corpus = "00 10 10 10 20 10 30 10 40 10 50 10 60 10 70 10 80 10 90 00"
        #   0  1  2  3  4  5  6  7  8  9 10 11 12 13 14 15 16 17 18 19
        tokens = corpus.split()
        iidx = InvertedIndex(tokens)
        g = GCL(iidx)

        outer = g.parse('"20" .. "50"')

        self.assertEqual(g.parse('"30" < %1', outer)._first_starting_at_or_after(0), (6, 6))
        self.assertEqual(g.parse('"30" < %1', outer)._first_starting_at_or_after(5), (6, 6))
        self.assertEqual(g.parse('"30" < %1', outer)._first_starting_at_or_after(6), (6, 6))
        self.assertEqual(g.parse('"30" < %1', outer)._first_starting_at_or_after(7), (INF, INF))
        self.assertEqual(g.parse('"20" < %1', outer)._first_starting_at_or_after(0), (4, 4))
        self.assertEqual(g.parse('"20" < %1', outer)._first_starting_at_or_after(3), (4, 4))
        self.assertEqual(g.parse('"20" < %1', outer)._first_starting_at_or_after(4), (4, 4))
        self.assertEqual(g.parse('"20" < %1', outer)._first_starting_at_or_after(5), (INF, INF))
        self.assertEqual(g.parse('"50" < %1', outer)._first_starting_at_or_after(0), (10, 10))
        self.assertEqual(g.parse('"50" < %1', outer)._first_starting_at_or_after(9), (10, 10))
        self.assertEqual(g.parse('"50" < %1', outer)._first_starting_at_or_after(10), (10, 10))
        self.assertEqual(g.parse('"50" < %1', outer)._first_starting_at_or_after(11), (INF, INF))

        self.assertEqual(g.parse('"30" < %1', outer)._first_ending_at_or_after(0), (6, 6))
        self.assertEqual(g.parse('"30" < %1', outer)._first_ending_at_or_after(5), (6, 6))
        self.assertEqual(g.parse('"30" < %1', outer)._first_ending_at_or_after(6), (6, 6))
        self.assertEqual(g.parse('"30" < %1', outer)._first_ending_at_or_after(7), (INF, INF))
        self.assertEqual(g.parse('"20" < %1', outer)._first_ending_at_or_after(0), (4, 4))
        self.assertEqual(g.parse('"20" < %1', outer)._first_ending_at_or_after(3), (4, 4))
        self.assertEqual(g.parse('"20" < %1', outer)._first_ending_at_or_after(4), (4, 4))
        self.assertEqual(g.parse('"20" < %1', outer)._first_ending_at_or_after(5), (INF, INF))
        self.assertEqual(g.parse('"50" < %1', outer)._first_ending_at_or_after(0), (10, 10))
        self.assertEqual(g.parse('"50" < %1', outer)._first_ending_at_or_after(9), (10, 10))
        self.assertEqual(g.parse('"50" < %1', outer)._first_ending_at_or_after(10), (10, 10))
        self.assertEqual(g.parse('"50" < %1', outer)._first_ending_at_or_after(11), (INF, INF))

    def test_trivial_corpus(self):
        corpus = "the quick brown fox jumps over the lazy dog and the brown dog runs away"
        tokens = corpus.split()
        iidx = InvertedIndex(tokens)
        g = GCL(iidx)

        # A random spattering of tests...

        self.assertEqual(list(g.Term("dog")), [slice(8, 9), slice(12, 13)])
        self.assertEqual(list(g.Term("cat")), [])
        self.assertEqual(list(g.Term("fox")), [slice(3, 4)])
        self.assertEqual(
            list(g.BoundedBy(g.Term("brown"), g.Term("dog"))), [slice(2, 9), slice(11, 13)]
        )
        self.assertEqual(
            list(g.Containing(g.BoundedBy(g.Term("brown"), g.Term("dog")), g.Term("over"))),
            [slice(2, 9)],
        )
        self.assertEqual(
            list(g.Containing(g.BoundedBy(g.Term("brown"), g.Term("dog")), g.Term("and"))), []
        )
        self.assertEqual(
            list(g.ContainedIn(g.Term("over"), g.BoundedBy(g.Term("brown"), g.Term("dog")))),
            [slice(5, 6)],
        )
        self.assertEqual(list(g.Phrase("quick", "brown", "fox")), [slice(1, 4)])
        self.assertEqual(list(g.Phrase("quick", "grey", "fox")), [])
        self.assertEqual(
            list(g.Containing(g.BoundedBy(g.Term("brown"), g.Term("dog")), g.Term("and"))), []
        )
        self.assertEqual(
            list(g.Containing(g.BoundedBy(g.Term("brown"), g.Term("dog")), g.Slice(slice(2, 3)))),
            [slice(2, 9)],
        )
        self.assertEqual(
            list(g.Containing(g.BoundedBy(g.Term("brown"), g.Term("dog")), g.Slice(slice(2, 9)))),
            [slice(2, 9)],
        )
        self.assertEqual(
            list(g.Containing(g.BoundedBy(g.Term("brown"), g.Term("dog")), g.Slice(slice(6, 7)))),
            [slice(2, 9)],
        )
        self.assertEqual(
            list(g.Containing(g.BoundedBy(g.Term("brown"), g.Term("dog")), g.Slice(slice(3, 5)))),
            [slice(2, 9)],
        )
        self.assertEqual(
            list(g.Containing(g.BoundedBy(g.Term("brown"), g.Term("dog")), g.Slice(slice(1, 5)))),
            [],
        )
        self.assertEqual(
            list(g.Containing(g.BoundedBy(g.Term("brown"), g.Term("dog")), g.Slice(slice(11, 12)))),
            [slice(11, 13)],
        )

        # Figure out
        # self.assertEqual(list( g.Containing(g.BoundedBy(g.Term('brown'), g.Term('dog')), g.Slice( slice(12,13) )) ), [slice(11,13)])

        # Remember, slice ends are open and do not include the end idx
        self.assertEqual(list(g.Length(1)), [slice(i, i + 1) for i in range(0, len(tokens))])
        self.assertEqual(list(g.Length(4)), [slice(i, i + 4) for i in range(0, len(tokens) - 3)])
        self.assertEqual(list(g.Length(len(tokens))), [slice(0, len(tokens))])
        self.assertEqual(list(g.Length(len(tokens) + 1)), [])
        self.assertEqual(
            list(g.Length(1).iterator(reverse=True)),
            [slice(i, i + 1) for i in range(len(tokens) - 1, -1, -1)],
        )
        self.assertEqual(
            list(g.Length(4).iterator(reverse=True)),
            [slice(i, i + 4) for i in range(len(tokens) - 4, -1, -1)],
        )
        self.assertEqual(
            list(g.Length(len(tokens)).iterator(reverse=True)), [slice(0, len(tokens))]
        )
        self.assertEqual(list(g.Length(len(tokens) + 1).iterator(reverse=True)), [])

        self.assertEqual(list(g.Start(g.Term("fox"))), [slice(3, 4)])
        self.assertEqual(list(g.End(g.Term("fox"))), [slice(3, 4)])

        self.assertEqual(list(g.Start(g.Phrase("quick", "brown", "fox"))), [slice(1, 2)])
        self.assertEqual(list(g.End(g.Phrase("quick", "brown", "fox"))), [slice(3, 4)])

        self.assertEqual(
            list(g.Start(g.Length(1))), [slice(i, i + 1) for i in range(0, len(tokens))]
        )
        self.assertEqual(
            list(g.Start(g.Length(4))), [slice(i, i + 1) for i in range(0, len(tokens) - 3)]
        )
        self.assertEqual(
            list(g.Start(g.Length(1)).iterator(reverse=True)),
            [slice(i, i + 1) for i in range(len(tokens) - 1, -1, -1)],
        )
        self.assertEqual(
            list(g.Start(g.Length(4)).iterator(reverse=True)),
            [slice(i, i + 1) for i in range(len(tokens) - 4, -1, -1)],
        )

        self.assertEqual(list(g.End(g.Length(1))), [slice(i, i + 1) for i in range(0, len(tokens))])
        self.assertEqual(
            list(g.End(g.Length(4))), [slice(i + 3, i + 4) for i in range(0, len(tokens) - 3)]
        )
        self.assertEqual(
            list(g.End(g.Length(1)).iterator(reverse=True)),
            [slice(i, i + 1) for i in range(len(tokens) - 1, -1, -1)],
        )
        self.assertEqual(
            list(g.End(g.Length(4)).iterator(reverse=True)),
            [slice(i + 3, i + 4) for i in range(len(tokens) - 4, -1, -1)],
        )
