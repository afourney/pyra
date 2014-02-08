INF = float('inf')

class InvertedIndex(object):

    def __init__(self, tokens):
        self.__postings = {}
        self.__corpus_length = 0

        for t in tokens:
            position = self.__corpus_length
            if t not in self.__postings:
                self.__postings[t] = []
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

        if position >= self.corpus_length() - 1:
            return INF

        # Not an efficient implementation!
        # TODO: Use binary search!
        idx = 0
        while idx < len(self.__postings[term]) and self.__postings[term][idx] <= position:
            idx += 1

        if idx >= len(self.__postings[term]):
            return INF
        else:
            return self.__postings[term][idx]


    def prev(self, term, position):

        if term not in self.__postings:
            return -INF

        if position <= 0:
            return -INF

        # Not an efficient implementation!
        # TODO: Use binary search!
        idx = len(self.__postings[term]) - 1
        while idx >= 0 and self.__postings[term][idx] >= position:
            idx -= 1

        if idx < 0:
            return -INF
        else:
            return self.__postings[term][idx]

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
