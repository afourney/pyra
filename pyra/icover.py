#!/usr/bin/python
"""Generate i-covers and rank passages by cover density."""

from math import log

INF = float("inf")


class CoverDensityRanking:
    """Rank query passages using i-covers and logarithmic scoring."""

    def __init__(self, inverted_index):
        """Store the inverted index used to generate and score passages."""
        self.__idx = inverted_index

    def iCovers(self, i, query):
        """Return a generator of passages covering i distinct query terms."""
        return CoverGenerator(self.__idx, i, query)

    def rank(self, query):
        """Return passage and score pairs in descending score order."""
        # Deduplicate the query
        q = {}
        for t in query:
            q[t] = 1
        query = q.keys()
        q = None

        results = []
        for i in range(0, len(query)):
            results.extend([(c, self.__score(c)) for c in self.iCovers(i + 1, query)])

        results = sorted(results, key=lambda x: x[1], reverse=True)
        return results

    def __score(self, icover):
        i = len(icover["terms"])
        length = icover["extent"][1] - icover["extent"][0] + 1
        N = self.__idx.corpus_length

        acc = 0
        for t in icover["terms"]:
            f = self.__idx.frequency(t)
            acc += log(float(N) / float(f), 2.0)
        return acc - i * log(length, 2.0)


class CoverGenerator:
    """Generate minimal passages containing at least i distinct query terms."""

    def __init__(self, inverted_index, i, query):
        """Store the index, required term count, and distinct query terms."""
        self.__idx = inverted_index
        self.__i = i
        self.__query = list(set(query))

    def __iter__(self):
        """Iterate over covers in forward order."""
        return self.iterator()

    @property
    def inverted_index(self):
        """Return the inverted index used by this generator."""
        return self.__idx

    def iterator(self, k=0, **args):
        """Iterate over covers starting at or after position k."""
        return CoverGenerator._forward_iterator(self, k)

    class _forward_iterator:
        def __init__(self, generator, k):
            self.__k = k
            self.__generator = generator

        def __iter__(self):
            return self

        def __next__(self):
            return self.next()

        def next(self):
            if self.__k == INF:
                raise StopIteration()

            r = self.__generator._first_starting_at_or_after(self.__k)
            u, _v = r["extent"]

            if u != INF:
                self.__k = u + 1
                return r  # _extent2slice( (u,v) )
            else:
                raise StopIteration()

    def _first_starting_at_or_after(self, k):
        r = []
        left_positions = []

        for _ in range(0, len(self.__query)):
            r.append(None)

        # Find the next location of each term in the query
        # then return the ith largest
        for i in range(0, len(self.__query)):
            r[i] = self._r(self.__query[i], k)
        r_sorted = sorted(r)
        q = r_sorted[self.__i - 1]

        # Figure out which of those terms are included
        terms = []
        for i in range(0, len(self.__query)):
            if r[i] <= q:
                terms.append(self.__query[i])

        for _ in range(0, len(terms)):
            left_positions.append(None)

        # Find the furthest term from q such that the
        # span includes all terms
        for i in range(0, len(terms)):
            left_positions[i] = self._l(terms[i], q)
        l_sorted = sorted(left_positions)

        extent = (l_sorted[0], q)
        if abs(extent[0]) == INF or abs(extent[1]) == INF:
            return {"extent": (INF, INF), "terms": terms}
        else:
            return {"extent": extent, "terms": terms}

    def _r(self, t, k):
        return self.inverted_index.next(t, k - 1)

    def _l(self, t, k):
        return self.inverted_index.prev(t, k + 1)


#
# Helper method for converting extents to python slices
#


def _extent2slice(extent):
    start = extent[0]
    stop = extent[1]

    if start == -INF:
        start = None

    if stop == INF:
        stop = None
    else:
        stop += 1

    return slice(start, stop)


def _slice2extent(s):
    start = s.start
    stop = s.stop

    if start is None:
        start = -INF

    if stop is None:
        stop = INF
    elif stop == 0:
        stop = -INF

    return (start, stop - 1)
