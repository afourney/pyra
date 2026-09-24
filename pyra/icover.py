#!/usr/bin/python
"""Generate i-covers and rank passages by cover density."""

from __future__ import annotations

from collections.abc import Hashable, Iterable, Iterator
from math import log
from typing import Self, TypedDict

from ._types import Extent, Position
from .iindex import InvertedIndex

INF = float("inf")


class Cover(TypedDict):
    """An exclusive-stop token slice and the query terms it covers."""

    slice: slice
    terms: list[Hashable]


class _ExtentCover(TypedDict):
    """An internal inclusive extent, including exhausted-search sentinels."""

    extent: Extent
    terms: list[Hashable]


class CoverDensityRanking:
    """Rank query passages using i-covers and logarithmic scoring."""

    def __init__(self, inverted_index: InvertedIndex) -> None:
        """Store the inverted index used to generate and score passages."""
        self.__idx = inverted_index

    def iCovers(self, i: int, query: Iterable[Hashable]) -> CoverGenerator:
        """Return a generator of passages covering i distinct query terms."""
        return CoverGenerator(self.__idx, i, query)

    def rank(self, query: Iterable[Hashable]) -> list[tuple[slice, float]]:
        """Return (slice, score) pairs in descending score order, with exclusive stops."""
        # Deduplicate the query
        q: dict[Hashable, int] = {}
        for t in query:
            q[t] = 1
        query = q.keys()

        results: list[tuple[slice, float]] = []
        for i in range(0, len(query)):
            results.extend([(c["slice"], self.__score(c)) for c in self.iCovers(i + 1, query)])

        results = sorted(results, key=lambda x: x[1], reverse=True)
        return results

    def __score(self, icover: Cover) -> float:
        i = len(icover["terms"])
        start, stop, _step = icover["slice"].indices(self.__idx.corpus_length)
        length = stop - start
        N = self.__idx.corpus_length

        acc = 0.0
        for t in icover["terms"]:
            f = self.__idx.frequency(t)
            acc += log(float(N) / float(f), 2.0)
        return acc - i * log(length, 2.0)


class CoverGenerator:
    """Generate minimal passages containing at least i distinct query terms."""

    def __init__(self, inverted_index: InvertedIndex, i: int, query: Iterable[Hashable]) -> None:
        """Store the index, required term count, and distinct query terms."""
        self.__idx = inverted_index
        self.__i = i
        self.__query = list(set(query))

    def __iter__(self) -> Iterator[Cover]:
        """Iterate over covers in forward order."""
        return self.iterator()

    @property
    def inverted_index(self) -> InvertedIndex:
        """Return the inverted index used by this generator."""
        return self.__idx

    def iterator(self, k: Position = 0, **args: object) -> Iterator[Cover]:
        """Iterate over covers starting at or after position k."""
        return CoverGenerator._forward_iterator(self, k)

    class _forward_iterator:
        def __init__(self, generator: CoverGenerator, k: Position) -> None:
            self.__k = k
            self.__generator = generator

        def __iter__(self) -> Self:
            return self

        def __next__(self) -> Cover:
            return self.next()

        def next(self) -> Cover:
            if self.__k == INF:
                raise StopIteration()

            r = self.__generator._first_starting_at_or_after(self.__k)
            u, v = r["extent"]

            if u != INF:
                self.__k = u + 1
                return {"slice": slice(int(u), int(v) + 1), "terms": r["terms"]}
            else:
                raise StopIteration()

    def _first_starting_at_or_after(self, k: Position) -> _ExtentCover:
        # Find the next location of each term in the query
        # then return the ith largest.
        r = [self._r(term, k) for term in self.__query]
        r_sorted = sorted(r)
        q = r_sorted[self.__i - 1]

        # Figure out which of those terms are included
        terms: list[Hashable] = []
        for i in range(0, len(self.__query)):
            if r[i] <= q:
                terms.append(self.__query[i])

        # Find the furthest term from q such that the span includes all terms.
        left_positions = [self._l(term, q) for term in terms]
        l_sorted = sorted(left_positions)

        extent = (l_sorted[0], q)
        if abs(extent[0]) == INF or abs(extent[1]) == INF:
            return {"extent": (INF, INF), "terms": terms}
        else:
            return {"extent": extent, "terms": terms}

    def _r(self, t: Hashable, k: Position) -> Position:
        return self.inverted_index.next(t, k - 1)

    def _l(self, t: Hashable, k: Position) -> Position:
        return self.inverted_index.prev(t, k + 1)


#
# Helper method for converting extents to python slices
#


# Retain these helpers for compatibility with existing callers.
def _extent2slice(extent: Extent) -> slice:  # pyright: ignore[reportUnusedFunction]
    start = extent[0]
    stop = extent[1]

    if start == -INF:
        start = None

    if stop == INF:
        stop = None
    else:
        stop += 1

    return slice(start, stop)


def _slice2extent(s: slice) -> Extent:  # pyright: ignore[reportUnusedFunction]
    start = s.start
    stop = s.stop

    if start is None:
        start = -INF

    if stop is None:
        stop = INF
    elif stop == 0:
        stop = -INF

    return (start, stop - 1)
