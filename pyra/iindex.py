from .util import galloping_search
from itertools import islice

INF = float('inf')

class InvertedIndex(object):

    def __init__(self, tokens):
        self.__postings = {}
        self.__corpus_length = 0
        self.__next_cache = {}
        self.__prev_cache = {}

        for t in tokens:
            position = self.__corpus_length
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
    def corpus_length(self):
        return self.__corpus_length


    def next(self, term, position):

        i = self.__inext(term, position)
        if abs(i) == INF:
            return i
        else:
            return self.__postings[term][i]


    def prev(self, term, position):

        i = self.__iprev(term, position)
        if abs(i) == INF:
            return i
        else:
            return self.__postings[term][i]


    #
    # Convenience methods that are never called when 
    # processing region algebra queries
    #

    def first(self, term):
        return self.next(term, -INF)


    def last(self, term):
        return self.prev(term, INF)


    def frequency(self, term, start=-INF, end=-INF):
        # Returns the frequency of the term between the
        # start and end positions (inclusive)

        if term not in self.__postings:
            return 0

        istart = self.__inext(term, start - 1)
        iend   = self.__iprev(term, end + 1)

        if istart == INF:
            return 0
        elif istart == -INF:
            istart = 0
         
        if iend == -INF:
            return 0
        elif iend == INF:
            iend = len(self.__postings[term]) - 1

        return iend - istart + 1


    def postings(self, term, start=None, **args):

        reverse = False
        for arg,val in args.items():
            if arg == "reverse":
                reverse = val
            else:
                raise ValueError()

        # Will return an iterator over the term's postings list

        if term not in self.__postings:
            return [].__iter__()
            
        if reverse:
            if start is None:
                start = INF

            istart = self.__iprev(term, start+1)

            def rev_it(pl,i):
                while i >= 0:
                    yield pl[i]
                    i -= 1
            
            return rev_it(self.__postings[term], istart)
        else:
            if start is None:
                start = -INF

            istart = self.__inext(term, start-1)

            def fwd_it(pl,i):
                while i < len(pl):
                    yield pl[i]
                    i += 1
            
            return fwd_it(self.__postings[term], istart)


    def dictionary(self):
        return set(self.__postings.keys())


    def __getitem__(self, term):
        return self.postings(term)


    def __iter__(self):
        return self.dictionary().__iter__()


    def __inext(self, term, position):

        if term not in self.__postings:
            return INF

        plist = self.__postings[term]

        if position >= plist[-1]:
            return INF

        if position < plist[0]:
            return 0

        # Reset the cache if our assumption of a 
        # forward scan is viloated
        if (self.__next_cache[term] > 0 and 
            plist[self.__next_cache[term]] > position):
           self.__next_cache[term] = 0

        i = galloping_search(plist, position, self.__next_cache[term]) 

        # position is in the list, at position i
        if plist[i] == position:
            self.__next_cache[term] = i+1
            return i+1
        # position not in list, and all positions from i to end
        # are larger
        else: 
            self.__next_cache[term] = i
            return i


    def __iprev(self, term, position):

        if term not in self.__postings:
            return -INF

        plist = self.__postings[term]

        if position <= plist[0]:
            return -INF

        if position > plist[-1]:
            return len(plist)-1

        # Reset the cache if our assumption of a 
        # backward scan is viloated
        if (self.__prev_cache[term] < len(plist)-1 and
            plist[self.__prev_cache[term]] < position):
           self.__prev_cache[term] = len(plist)-1

        i = galloping_search(plist, position, self.__prev_cache[term]) 

        # position is in the list, at position i
        if plist[i] == position:
            self.__prev_cache[term] = i-1
            return i-1
        # position not in list, and all positions from i to end
        # are larger
        else:
            self.__prev_cache[term] = i-1
            return i-1
