"""Index term positions and sparse source checkpoints."""

from __future__ import annotations

from collections.abc import Hashable, Iterable, Iterator
from typing import cast

from ._types import Position
from .util import galloping_search

INF = float("inf")
_CHECKPOINT_STRIDE = 256


class InvertedIndex:
    """Index plain terms or (string term, integer source offset) pairs.

    Input is consumed once and must not mix the two forms. Source offsets
    must be nondecreasing; they are opaque integers, independent of the
    consecutive token positions stored in postings. Two-element tuples
    beginning with a string are reserved for the source-offset form.
    """

    def __init__(self, tokens: Iterable[Hashable]) -> None:
        """Build postings and optional source checkpoints from a single token pass."""
        self.__postings: dict[Hashable, list[int]] = {}
        self.__corpus_length = 0
        self.__next_cache: dict[Hashable, int] = {}
        self.__prev_cache: dict[Hashable, int] = {}
        self.__has_offsets = False
        self.__checkpoint_offsets: list[int] | None = None
        previous_offset = None

        for t in tokens:
            position = self.__corpus_length
            pair = cast(tuple[object, ...], t) if isinstance(t, tuple) else ()
            has_offset = len(pair) == 2 and isinstance(pair[0], str)
            if position == 0:
                self.__has_offsets = has_offset
                if has_offset:
                    self.__checkpoint_offsets = []
            elif has_offset != self.__has_offsets:
                raise ValueError("cannot mix plain terms and terms with source offsets")

            if has_offset:
                t, offset = cast(tuple[str, object], pair)
                if not isinstance(offset, int) or isinstance(offset, bool):
                    raise TypeError("source offsets must be integers (not booleans)")
                if previous_offset is not None and offset < previous_offset:
                    raise ValueError("source offsets must be nondecreasing")
                previous_offset = offset
                if position % _CHECKPOINT_STRIDE == 0:
                    assert self.__checkpoint_offsets is not None
                    self.__checkpoint_offsets.append(offset)

            if t not in self.__postings:
                self.__postings[t] = []
                self.__next_cache[t] = 0
                self.__prev_cache[t] = 0
            self.__postings[t].append(position)
            self.__corpus_length += 1

    #
    # Core methods required to support the region algebra
    #

    @property
    def corpus_length(self) -> int:
        """Return the number of indexed tokens."""
        return self.__corpus_length

    def next(self, term: Hashable, position: Position) -> Position:
        """Return the first occurrence strictly after position, or positive infinity."""
        i = self.__inext(term, position)
        if abs(i) == INF:
            return i
        else:
            return self.__postings[term][cast(int, i)]

    def prev(self, term: Hashable, position: Position) -> Position:
        """Return the last occurrence strictly before position, or negative infinity."""
        i = self.__iprev(term, position)
        if abs(i) == INF:
            return i
        else:
            return self.__postings[term][cast(int, i)]

    #
    # Convenience methods that are never called when
    # processing region algebra queries
    #

    def checkpoint(self, position: int) -> tuple[int, int]:
        """Return the nearest checkpoint at or before a token position.

        The returned pair is (checkpoint_token_position, source_offset).
        Plain terms return (position, position) without storing checkpoints.

        The inclusive range 0 <= position <= corpus_length is valid. At the
        end boundary, explicit-offset input returns its last checkpoint.
        An empty index returns (0, 0) for position 0.

        Raise TypeError for non-integers (including booleans), or IndexError
        for positions outside the valid range.
        """
        # Keep runtime validation for callers that do not use a type checker.
        if not isinstance(position, int) or isinstance(position, bool):  # pyright: ignore[reportUnnecessaryIsInstance]
            raise TypeError("checkpoint position must be an integer (not a boolean)")
        if position < 0 or position > self.__corpus_length:
            raise IndexError("checkpoint position outside the corpus")
        if not self.__has_offsets:
            return (position, position)

        assert self.__checkpoint_offsets is not None
        i = min(position // _CHECKPOINT_STRIDE, len(self.__checkpoint_offsets) - 1)
        return (i * _CHECKPOINT_STRIDE, self.__checkpoint_offsets[i])

    def first(self, term: Hashable) -> Position:
        """Return the first occurrence of term, or positive infinity."""
        return self.next(term, -INF)

    def last(self, term: Hashable) -> Position:
        """Return the last occurrence of term, or negative infinity."""
        return self.prev(term, INF)

    def frequency(self, term: Hashable, start: Position = -INF, end: Position = INF) -> int:
        """Return the number of occurrences within the inclusive start and end bounds."""
        # Returns the frequency of the term between the
        # start and end positions (inclusive)

        if term not in self.__postings:
            return 0

        istart = self.__inext(term, start - 1)
        iend = self.__iprev(term, end + 1)

        if istart == INF:
            return 0
        elif istart == -INF:
            istart = 0

        if iend == -INF:
            return 0
        elif iend == INF:
            iend = len(self.__postings[term]) - 1

        return cast(int, iend - istart + 1)

    def postings(
        self, term: Hashable, start: Position | None = None, **args: bool
    ) -> Iterator[int]:
        """Iterate over term positions from start, optionally in reverse order."""
        reverse = False
        for arg, val in args.items():
            if arg == "reverse":
                reverse = val
            else:
                raise ValueError()

        # Will return an iterator over the term's postings list

        if term not in self.__postings:
            return iter(())

        if reverse:
            if start is None:
                start = INF

            istart = self.__iprev(term, start + 1)

            def rev_it(pl: list[int], i: Position) -> Iterator[int]:
                while i >= 0:
                    yield pl[cast(int, i)]
                    i -= 1

            return rev_it(self.__postings[term], istart)
        else:
            if start is None:
                start = -INF

            istart = self.__inext(term, start - 1)

            def fwd_it(pl: list[int], i: Position) -> Iterator[int]:
                while i < len(pl):
                    yield pl[cast(int, i)]
                    i += 1

            return fwd_it(self.__postings[term], istart)

    def dictionary(self) -> set[Hashable]:
        """Return the set of indexed terms."""
        return set(self.__postings.keys())

    def __getitem__(self, term: Hashable) -> Iterator[int]:
        """Iterate over the postings for term."""
        return self.postings(term)

    def __iter__(self) -> Iterator[Hashable]:
        """Iterate over the indexed terms."""
        return self.dictionary().__iter__()

    def __inext(self, term: Hashable, position: Position) -> Position:

        if term not in self.__postings:
            return INF

        plist = self.__postings[term]

        if position >= plist[-1]:
            return INF

        if position < plist[0]:
            return 0

        # Reset the cache if our assumption of a
        # forward scan is viloated
        if self.__next_cache[term] > 0 and plist[self.__next_cache[term]] > position:
            self.__next_cache[term] = 0

        i = galloping_search(plist, position, self.__next_cache[term])

        # position is in the list, at position i
        if plist[i] == position:
            self.__next_cache[term] = i + 1
            return i + 1
        # position not in list, and all positions from i to end
        # are larger
        else:
            self.__next_cache[term] = i
            return i

    def __iprev(self, term: Hashable, position: Position) -> Position:

        if term not in self.__postings:
            return -INF

        plist = self.__postings[term]

        if position <= plist[0]:
            return -INF

        if position > plist[-1]:
            return len(plist) - 1

        # Reset the cache if our assumption of a
        # backward scan is viloated
        if self.__prev_cache[term] < len(plist) - 1 and plist[self.__prev_cache[term]] < position:
            self.__prev_cache[term] = len(plist) - 1

        i = galloping_search(plist, position, self.__prev_cache[term])

        # position is in the list, at position i
        if plist[i] == position:
            self.__prev_cache[term] = i - 1
            return i - 1
        # position not in list, and all positions from i to end
        # are larger
        else:
            self.__prev_cache[term] = i - 1
            return i - 1
