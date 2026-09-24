import unittest

from pyra import CoverDensityRanking, GCL, InvertedIndex
from pyra.iindex import _CHECKPOINT_STRIDE


class TestCheckpointContract(unittest.TestCase):
    def test_plain_terms_use_identity_mapping(self):
        index = InvertedIndex("a b a".split())
        for position in (3, 0, 2, 1, 3):
            self.assertEqual(index.checkpoint(position), (position, position))
        self.assertEqual(list(index.postings("a")), [0, 2])

    def test_empty_and_single_token(self):
        empty = InvertedIndex(iter(()))
        self.assertEqual(empty.corpus_length, 0)
        self.assertEqual(empty.checkpoint(0), (0, 0))
        for position in (-1, 1):
            with self.assertRaises(IndexError):
                empty.checkpoint(position)

        positioned = InvertedIndex(iter([("a", 37)]))
        self.assertEqual(positioned.checkpoint(0), (0, 37))
        self.assertEqual(positioned.checkpoint(1), (0, 37))

    def test_one_shot_input_is_consumed_once(self):
        class OneShot:
            def __init__(self, items):
                self.items = iter(items)
                self.started = False

            def __iter__(self):
                if self.started:
                    raise AssertionError("input was iterated twice")
                self.started = True
                return self

            def __next__(self):
                return next(self.items)

            def __len__(self):
                raise AssertionError("input length was requested")

        for items, expected in [(["a", "b"], (1, 1)),
                                ([("a", 40), ("b", 90)], (0, 40))]:
            with self.subTest(items=items):
                source = OneShot(items)
                index = InvertedIndex(source)
                self.assertEqual(index.corpus_length, 2)
                with self.assertRaises(StopIteration):
                    next(source)
                del source
                self.assertEqual(index.checkpoint(1), expected)

    def test_positions_and_search_behavior_are_unchanged(self):
        terms = "a b x a b b".split()
        plain = InvertedIndex(terms)
        positioned = InvertedIndex((term, 100 + p * 17)
                                   for p, term in enumerate(terms))
        self.assertEqual(positioned.corpus_length, plain.corpus_length)
        self.assertEqual(positioned.dictionary(), plain.dictionary())
        for term in ("a", "b", "x", "missing"):
            with self.subTest(term=term):
                self.assertEqual(list(positioned[term]), list(plain[term]))
                self.assertEqual(list(positioned.postings(term, reverse=True)),
                                 list(plain.postings(term, reverse=True)))
                self.assertEqual(positioned.first(term), plain.first(term))
                self.assertEqual(positioned.last(term), plain.last(term))
                self.assertEqual(positioned.frequency(term), plain.frequency(term))
                self.assertEqual(positioned.frequency(term, 1, 4),
                                 plain.frequency(term, 1, 4))
                for p in (3, 0, 5, -1, 2, 6):
                    self.assertEqual(positioned.next(term, p), plain.next(term, p))
                    self.assertEqual(positioned.prev(term, p), plain.prev(term, p))

        for index in (plain, positioned):
            gcl = GCL(index)
            phrase = gcl.Phrase("a", "b")
            self.assertEqual(list(phrase), [slice(0, 2), slice(3, 5)])
            self.assertEqual(list(phrase.iterator(reverse=True)),
                             [slice(3, 5), slice(0, 2)])
            self.assertEqual(list(gcl.Length(3)),
                             [slice(p, p + 3) for p in range(4)])
        self.assertEqual(CoverDensityRanking(positioned).rank(["a", "b"]),
                         CoverDensityRanking(plain).rank(["a", "b"]))

    def test_other_hashable_plain_terms_keep_identity_mapping(self):
        terms = [42, (1, 2), ("a",), ("a", "b", "c"), None, 42]
        index = InvertedIndex(terms)
        self.assertEqual(list(index.postings(42)), [0, 5])
        self.assertEqual(index.dictionary(), set(terms))
        for p in range(len(terms) + 1):
            self.assertEqual(index.checkpoint(p), (p, p))

    def test_mixed_modes_are_rejected(self):
        for items in (["a", ("b", 10)], [("a", 10), "b"]):
            with self.subTest(items=items), self.assertRaises(ValueError):
                InvertedIndex(iter(items))

    def test_invalid_offsets_are_rejected(self):
        for offset in (True, False, 1.0, "1", None, float("inf"), [], (1,)):
            for prefix in ([], [("a", 0)]):
                with self.subTest(offset=offset, prefix=prefix):
                    with self.assertRaises(TypeError):
                        InvertedIndex(prefix + [("b", offset)])

    def test_invalid_checkpoint_positions_are_rejected(self):
        for index in (InvertedIndex([]), InvertedIndex(["a"]),
                      InvertedIndex([("a", 10)])):
            for p in (True, False, 0.0, "0", None, float("inf"), float("nan")):
                with self.subTest(length=index.corpus_length, position=p):
                    with self.assertRaises(TypeError):
                        index.checkpoint(p)
            for p in (-1, index.corpus_length + 1):
                with self.assertRaises(IndexError):
                    index.checkpoint(p)


class TestCheckpointStorage(unittest.TestCase):
    """Tests specific to the private fixed-stride representation."""

    def test_identity_mapping_has_no_checkpoint_array(self):
        for terms in ([], ["a"] * 1000):
            index = InvertedIndex(terms)
            self.assertFalse(index._InvertedIndex__has_offsets)
            self.assertIsNone(index._InvertedIndex__checkpoint_offsets)

    def test_sparse_offsets_and_end_boundary(self):
        stride = _CHECKPOINT_STRIDE
        for length in (1, stride - 1, stride, stride + 1, 2 * stride):
            offsets = [100 + p * p for p in range(length)]
            index = InvertedIndex(("a", offset) for offset in offsets)
            self.assertEqual(index._InvertedIndex__checkpoint_offsets,
                             offsets[::stride])
            self.assertEqual(index.checkpoint(0), (0, offsets[0]))
            for p in (stride - 1, stride, stride + 1):
                if p < length:
                    expected_token = 0 if p < stride else stride
                    self.assertEqual(index.checkpoint(p),
                                     (expected_token, offsets[expected_token]))
            self.assertEqual(index.checkpoint(length), index.checkpoint(length - 1))
            self.assertLess(index.checkpoint(length)[0], length)

    def test_signed_repeated_and_large_offsets(self):
        stride = _CHECKPOINT_STRIDE
        offsets = [-10] * stride + [2 ** 100] * (stride + 1)
        index = InvertedIndex(("a", offset) for offset in offsets)
        self.assertEqual(index.checkpoint(0), (0, -10))
        self.assertEqual(index.checkpoint(stride), (stride, 2 ** 100))
        self.assertEqual(index.checkpoint(2 * stride), (2 * stride, 2 ** 100))

    def test_decreasing_offsets_are_rejected_even_between_checkpoints(self):
        for p in (1, _CHECKPOINT_STRIDE, _CHECKPOINT_STRIDE + 1):
            with self.subTest(position=p), self.assertRaises(ValueError):
                InvertedIndex(("a", offset) for offset in [10] * p + [9])
