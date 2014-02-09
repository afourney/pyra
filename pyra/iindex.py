from .util import galloping_search

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

    def corpus_length(self):
        return self.__corpus_length


    def next(self, term, position):

        if term not in self.__postings:
            return INF

        plist = self.__postings[term]

        if position >= plist[-1]:
            return INF

        if position < plist[0]:
            return plist[0]

        # Reset the cache if our assumption of a 
        # forward scan is viloated
        if (self.__next_cache[term] > 0 and 
            plist[self.__next_cache[term]] > position):
           self.__next_cache[term] = 0

        i = galloping_search(plist, position, self.__next_cache[term]) 

        # position is in the list, at position i
        if plist[i] == position:
            self.__next_cache[term] = i+1
            return plist[i+1]
        # position not in list, and all positions from i to end
        # are larger
        else: 
            self.__next_cache[term] = i
            return plist[i]


    def prev(self, term, position):

        if term not in self.__postings:
            return -INF

        plist = self.__postings[term]

        if position <= plist[0]:
            return -INF

        if position > plist[-1]:
            return plist[-1]

        # Reset the cache if our assumption of a 
        # backward scan is viloated
        if (self.__prev_cache[term] < len(plist)-1 and
            plist[self.__prev_cache[term]] < position):
           self.__prev_cache[term] = len(plist)-1

        i = galloping_search(plist, position, self.__prev_cache[term]) 

        # position is in the list, at position i
        if plist[i] == position:
            self.__prev_cache[term] = i-1
            return plist[i-1]
        # position not in list, and all positions from i to end
        # are larger
        else:
            self.__prev_cache[term] = i-1
            return plist[i-1]


    #
    # Convenience methods that are never called when 
    # processing region algebra queries
    #

    def first(self, term):
        return self.next(term, -INF)


    def last(self, term):
        return self.prev(term, INF)


    def frequency(self, term, start=-INF, end=-INF):
        # Will return the frequency of the term between the
        # start and end positions (inclusive)

        # This can be done more efficiently than iterating over 
        # the postings list by subtracting indices of the
        # start and end positions in the posting list
        raise NotImplementedError()


    def postings(self, term, start=-INF, **args):

        reverse = False
        for arg,val in args.items():
            if arg == "reverse":
                reverse = val
            else:
                raise ValueError()

        # Will return an iterator over the term's postings list
        raise NotImplementedError()


    def dictionary(self):
        return set(self.__postings.keys())


    def __getitem__(self, term):
        return self.postings(term)


    def __iter__(self):
        return self.dictionary().__iter__()
