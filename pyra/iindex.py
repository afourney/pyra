from util import galloping_search

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


    def postings(self, term, start_position, end_position):
        # TODO: Make start and end consistent with the extents used / returned 
        #       by the query algebra.

        if term not in self.__postings:
            return []

        if start_position < 0:
            start_position = 0
        else:
            start_position = int(start_position)

        if end_position >= self.corpus_length():
            end_position = self.corpus_length() - 1
        else:
            end_position = int(end_position)

        results = []
        for p in self.__postings[term]:
            if start_position <= p and p <= end_position:
                results.append(p)
        return results


    def postings_count(self, term, start_position, end_position):
        # TODO: Make start and end consistent with the extents used / returned 
        #       by the query algebra.

        count = 0

        if term not in self.__postings:
            return count

        if start_position < 0:
            start_position = 0
        else:
            start_position = int(start_position)

        if end_position >= self.corpus_length():
            end_position = self.corpus_length() - 1
        else:
            end_position = int(end_position)

        results = []
        for p in self.__postings[term]:
            if start_position <= p and p <= end_position:
                count += 1
        return count


    def dictionary(self):
        return set(self.__postings.keys())
