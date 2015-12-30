#!/usr/bin/python

INF = float('inf')

class CoverDensityRanking(object):

    def __init__(self, inverted_index):
        self.__idx = inverted_index

    def iCovers(self, i, query):
        return CoverGenerator(self.__idx, i, query)


class CoverGenerator(object):

    def __init__(self, inverted_index, i, query):
        self.__idx  = inverted_index
        self.__i    = i
        self.__query = [ l for l in set(query) ]

    def __iter__(self):
        return self.iterator()

    @property
    def inverted_index(self):
        return self.__idx

    def iterator(self, k=None, **args):
        return GCListGenerator._forward_iterator(self, k)

    class _forward_iterator(object):
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

            u,v = self.__generator._first_starting_at_or_after(self.__k)

            if u != INF:
                self.__k = u + 1
                return _extent2slice( (u,v) )
            else:
                raise StopIteration()


    def _first_starting_at_or_after(self, k):
        r = list()
        l = list()

        for i in range(0, len(self.__query)):
            r.append(None)
        
        # Find the next location of each term in the query
        # then return the ith largest
        for i in range(0, len(self.__query)):
            r[i] = self._r(self.__query[i], k)
        r_sorted = sorted(r)
        q = r_sorted[self.__i-1]

        # Figure out which of those terms are included
        terms = list()
        for i in range(0, len(self.__query)):
            if r[i] <= q:
                terms.append(self.__query[i])

        for i in range(0, len(terms)):
            l.append(None)

        # Find the the furhtest term from q such that the 
        # span includes all terms
        for i in range(0, len(terms)):
            l[i] = self._l(terms[i], q)
        l_sorted = sorted(l)

        extent = (l_sorted[0], q)
        if abs(extent[0]) == INF or abs(extent[1]) == INF:
            return (INF, INF)
        else:
            return extent


    def _r(self, t, k):
        return self.inverted_index.next(t,k-1)

    def _l(self, t, k):
        return self.inverted_index.prev(t,k+1)

#
# Helper method for converting extents to python slices
#

def _extent2slice( extent ):
    start = extent[0]
    stop  = extent[1]

    if start == -INF:
        start = None

    if stop == INF:
        stop = None
    else:
        stop += 1

    return slice(start,stop)


def _slice2extent( s ):
    start = s.start
    stop  = s.stop

    if start is None:
        start = -INF

    if stop is None:
        stop = INF
    elif stop == 0:
        stop = -INF

    return (start, stop-1)
