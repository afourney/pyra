#!/usr/bin/python

INF = float('inf')

class GCL(object):

    def __init__(self, inverted_index):
        self.__idx = inverted_index

    def Phrase( self, *tokens ):
        return PhraseGenerator(self.__idx, *tokens)

    def List( self, *l ):
        return ListGenerator(self.__idx, *l)

    def Length( self, length ):
        raise NotImplementedError()

    def And( self, a, b ):
        raise NotImplementedError()

    def Or( self, a, b ):
        raise NotImplementedError()

    def BoundedBy( self, a, b ):
        return BoundedByGenerator(self.__idx, a, b)

    def Containing( self, a, b ):
        return ContainingGenerator(self.__idx, a, b)

    def ContainedIn( self, a, b ):
        raise NotImplementedError()

    def NotContaining( self, a, b ):
        raise NotImplementedError()

    def NotContainedIn( self, a, b ):
        raise NotImplementedError()

    #
    # Convenience method
    #
    def Term( self, term ):
        return self.Phrase(term)

    def Position( self, p ):
        return self.List( (p,p) )

    def Extent( self, e ):
        return self.List( e )




class GCListGenerator(object):

    def __init__(self, inverted_index):
        self.__idx = inverted_index

    def __iter__(self):
        return self.iterator()

    @property
    def inverted_index(self):
        return self.__idx

    def iterator(self, k=0):
        return GCListGenerator._forward_iterator(self, k)

    def reverse(self, k=None):
        if k is None:
            k = self.__idx.corpus_length()-1
        return GCListGenerator._reverse_iterator(self, k)

    def _first_starting_at_or_after(self, k):
        raise NotImplementedError()
        
    def _first_ending_at_or_after(self, k):
        raise NotImplementedError()

    def _last_ending_at_or_before(self, k):
        raise NotImplementedError()

    def _last_starting_at_or_before(self, k):
        raise NotImplementedError()


    class _forward_iterator(object):

        def __init__(self, generator, k):
            self.__k = k
            self.__generator = generator

        def __iter__(self):
            return self

        def __next__(self):
            self.next()

        def next(self):
            if self.__k == INF:
                raise StopIteration()

            u,v = self.__generator._first_starting_at_or_after(self.__k)

            if u != INF:
                result = _extent2slice( (u,v) )
                self.__k = u + 1
                return result
            else:
                raise StopIteration()


    class _reverse_iterator(object):

        def __init__(self, generator, k):
            self.__k = k
            self.__generator = generator

        def __iter__(self):
            return self

        def __next__(self):
            self.next()

        def next(self):
            if self.__k < 0:
                raise StopIteration()

            u,v = self.__generator._last_ending_on_or_before(self.__k)

            if u >= 0:
                result = _extent2slice( (u,v) )
                self.__k = v - 1
                return result
            else:
                raise StopIteration()

class ListGenerator(GCListGenerator):

    def __init__(self, inverted_index, *l):
        super(ListGenerator, self).__init__(inverted_index)
        self.__list = l

    def _first_starting_at_or_after(self, k):
        # First interval starting at or after k
        # TODO: Use binary search
        for i in range(0, len(self.__list)):
            if self.__list[i][0] >= k:
                return self.__list[i]
        return (INF,INF)
        

    def _first_ending_at_or_after(self, k):
        # First interval starting at or after k
        # TODO: Use binary search
        for i in range(0, len(self.__list)):
            if self.__list[i][1] >= k:
                return self.__list[i]
        return (INF,INF)

    def _last_ending_at_or_before(self, k):
        # Last interval ending at or before k
        # TODO: Use binary search
        for i in range(len(self.__list)-1,-1,-1):
            if self.__list[i][1] <= k:
                return self.__list[i]
        return (-INF,-INF)

    def _last_starting_at_or_before(self, k):
        # Last interval starting at or before k
        # TODO: Use binary search
        for i in range(len(self.__list)-1,-1,-1):
            if self.__list[i][0] <= k:
                return self.__list[i]
        return (-INF,-INF)

    # Helper methods for phrases
    def __next_phrase(self, tokens, position):
        v = position
        for i in range(0, len(tokens)):
            v = self.inverted_index.next(tokens[i], v)
        if v == INF:
            return (INF, INF)
        u = v
        for i in range(len(tokens)-2,-1,-1):
            u = self.inverted_index.prev(tokens[i], u)
        if v-u == len(tokens)-1:
            return (u,v)
        else:
            return self.__next_phrase(tokens, u)

    def __prev_phrase(self, tokens, position):
        v = position
        for i in range(len(tokens)-1,-1,-1):
            v = self.inverted_index.prev(tokens[i], v)
        if v == -INF:
            return (-INF, -INF)
        u = v
        for i in range(1,len(tokens)):
            u = self.inverted_index.next(tokens[i], u)
        if u-v == len(tokens)-1:
            return (v,u)
        else:
            return self.__prev_phrase(tokens, u)



class PhraseGenerator(GCListGenerator):

    def __init__(self, inverted_index, *tokens):
        super(PhraseGenerator, self).__init__(inverted_index)
        self.__phrase = tokens

    def _first_starting_at_or_after(self, k):
        if k == 0:
            return self.__next_phrase(self.__phrase,-INF)
        else:
            return self.__next_phrase(self.__phrase,k-1)
        
    def _first_ending_at_or_after(self, k):
        return self.__next_phrase(self.__phrase, k - len(self.__phrase))

    def _last_ending_at_or_before(self, k):
        return self.__prev_phrase(self.__phrase, k - len(self.__phrase) + 2)

    def _last_starting_at_or_before(self, k):
        return self.__prev_phrase(self.__phrase,k+1)

    # Helper methods for phrases
    def __next_phrase(self, tokens, position):
        v = position
        for i in range(0, len(tokens)):
            v = self.inverted_index.next(tokens[i], v)
        if v == INF:
            return (INF, INF)
        u = v
        for i in range(len(tokens)-2,-1,-1):
            u = self.inverted_index.prev(tokens[i], u)
        if v-u == len(tokens)-1:
            return (u,v)
        else:
            return self.__next_phrase(tokens, u)

    def __prev_phrase(self, tokens, position):
        v = position
        for i in range(len(tokens)-1,-1,-1):
            v = self.inverted_index.prev(tokens[i], v)
        if v == -INF:
            return (-INF, -INF)
        u = v
        for i in range(1,len(tokens)):
            u = self.inverted_index.next(tokens[i], u)
        if u-v == len(tokens)-1:
            return (v,u)
        else:
            return self.__prev_phrase(tokens, u)


class BoundedByGenerator(GCListGenerator):


    def __init__(self, inverted_index, a, b):
        super(BoundedByGenerator, self).__init__(inverted_index)
        self.__a = a
        self.__b = b


    def _first_starting_at_or_after(self, k):
        a = self.__a
        b = self.__b

        u0,v0 = a._first_starting_at_or_after(k)
        if u0 == INF and v0 == INF:
            return (INF,INF)

        u1,v1 = b._first_starting_at_or_after(v0+1)
        if u1 == INF and v1 == INF:
            return (INF,INF)

        u2,v2 = a._last_ending_at_or_before(u1-1)
        return (u2,v1)
        

    def _first_ending_at_or_after(self, k):
        a = self.__a
        b = self.__b

        #1. Skip forwards to find the first interval matching a
        u0,v0 = a.first_ending_at_or_after(k)
        if u0 == INF and v0 == INF:
            return (INF,INF)

        #2. Skip forward to find the first interval matching b after 1.
        u1,v1 = b.first_starting_at_or_after(v0+1)
        if u1 == INF and v1 == INF:
            return (INF,INF)

        #3. Skip backwards to find the last interval matching a ending before 2.
        u2,v2 = a.last_ending_at_or_before(u1-1)

        return (u2,v1)


    def _last_ending_at_or_before(self, k):
        a = self.__a
        b = self.__b
        raise NotImplementedError()


    def _last_starting_at_or_before(self, k):
        a = self.__a
        b = self.__b
        raise NotImplementedError()


class ContainingGenerator(GCListGenerator):

    def __init__(self, inverted_index, a, b):
        super(ContainingGenerator, self).__init__(inverted_index)
        self.__a = a
        self.__b = b

    def _first_starting_at_or_after(self, k):
        a = self.__a
        b = self.__b

        # Get the first candidate match for A
        u0,v0 = a._first_starting_at_or_after(k)
        if u0 == INF and v0 == INF:
            return (INF,INF)

        # Get the first candidate match for B
        u1,v1 = b._first_starting_at_or_after(u0)
        if u1 == INF and v1 == INF:
            return (INF,INF)

        # We know u1 >= u0
        # Check containment by verifying that v1 <= v0
        if v1 <= v0:
             return (u0,v0)
        else:
            # Keep looking
            return self._first_starting_at_or_after(v0+1)
        

    def _first_ending_at_or_after(self, k):
        a = self.__a
        b = self.__b

        # Get the first candidate match for A
        u0,v0 = a._first_ending_at_ot_after(k)
        if u0 == INF and v0 == INF:
            return (INF,INF)

        # Get the first candidate match for B
        u1,v1 = b._first_starting_at_or_after(u0)
        if u1 == INF and v1 == INF:
            return (INF,INF)

        # We know u1 >= u0
        # Check containment by verifying that v1 <= v0
        if v1 <= v0:
            return (u0,v0)
        else:
            # Keep looking
            return self._first_ending_at_or_after(v0+1)


    def _last_ending_at_or_before(self, k):
        a = self.__a
        b = self.__b
        raise NotImplementedError()

    def _last_starting_at_or_before(self, k):
        a = self.__a
        b = self.__b
        raise NotImplementedError()


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

