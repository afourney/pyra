#!/usr/bin/python

INF = float('inf')

class GCL(object):

    def __init__(self, inverted_index):
        self.__idx = inverted_index

    #
    # Elementary Generators
    #

    def Term( self, term ):
        return self.Phrase(term)

   
    def Phrase( self, *tokens ):
        return PhraseGenerator(self.__idx, *tokens)


    def Position( self, p ):
        return ListGenerator(self.__idx, (p,p) )


    def Slice( self, s ):
        return ListGenerator(self.__idx, _slice2extent(s))


    def Length( self, length ):
        return FixedLengthGenerator(self.__idx, length)

    #
    # Binary Operators
    #
    def And( self, a, b ):
        raise NotImplementedError()

    def Or( self, a, b ):
        raise NotImplementedError()

    def BoundedBy( self, a, b ):
        return BoundedByOperator(self.__idx, a, b)

    def Containing( self, a, b ):
        return ContainedByOperator(self.__idx, a, b)

    def ContainedIn( self, a, b ):
        raise NotImplementedError()

    def NotContaining( self, a, b ):
        raise NotImplementedError()

    def NotContainedIn( self, a, b ):
        raise NotImplementedError()

    # #
    # # Unary operators
    # #
    # def Start( self, a ):
    #     return StartOperator(self.__idx, a)

    # def End( self, a ):
    #     return EndOperator(self.__idx, a)

   


class GCListGenerator(object):

    def __init__(self, inverted_index):
        self.__idx = inverted_index

    def __iter__(self):
        return self.iterator()

    @property
    def inverted_index(self):
        return self.__idx


    def iterator(self, k=None, **args):

        reverse = False
        
        for arg,val in args.items():
            if arg == "reverse":
                reverse = val
            else:
                raise ValueError()

        if reverse:
            if k is None:
                k = self.__idx.corpus_length()-1
            return GCListGenerator._reverse_iterator(self, k)
        else:
            if k is None:
                k = 0
            return GCListGenerator._forward_iterator(self, k)


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


    class _reverse_iterator(object):

        def __init__(self, generator, k):
            self.__k = k
            self.__generator = generator

        def __iter__(self):
            return self

        def __next__(self):
            return self.next()

        def next(self):
            if self.__k < 0:
                raise StopIteration()

            u,v = self.__generator._last_ending_at_or_before(self.__k)

            if u >= 0:
                self.__k = v - 1
                return _extent2slice( (u,v) )
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


class FixedLengthGenerator(GCListGenerator):

    def __init__(self, inverted_index, length):
        super(FixedLengthGenerator, self).__init__(inverted_index)
        self.__length = length

    def _first_starting_at_or_after(self, k):
        v = k + self.__length - 1

        # Overflow, no way to fix
        if v >= self.inverted_index.corpus_length():
            return (INF, INF)
        else:
            return (k, v)
        
    def _first_ending_at_or_after(self, k):
        u = k - self.__length + 1 

        # Underflow, try to fix
        if u < 0:
            d = 0 - u
            k += d
            u += d

            if k >= self.inverted_index.corpus_length():
                return (INF, INF)
            else:
                return (u, k)
        else:
            return (u, k)


    def _last_ending_at_or_before(self, k):
        u = k - self.__length + 1 

        # Underflow, no way to fix
        if u < 0:
            return (-INF, -INF)
        else:
            return (u, k)


    def _last_starting_at_or_before(self, k):
        v = k + self.__length - 1

        # Overflowed, try to fix!
        if v >= self.inverted_index.corpus_length():
            d = v - self.inverted_indec.corpus_lenght() + 1
            k -= d
            v -= d

            if u < 0:
                return (-INF, -INF)
            else:
                return (k, v)
        else:
            return (k, v)
 

class BoundedByOperator(GCListGenerator):


    def __init__(self, inverted_index, a, b):
        super(BoundedByOperator, self).__init__(inverted_index)
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


class ContainedByOperator(GCListGenerator):

    def __init__(self, inverted_index, a, b):
        super(ContainedByOperator, self).__init__(inverted_index)
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


# class StartOperator(GCListGenerator):

#     def __init__(self, inverted_index, a):
#         super(StartOperator, self).__init__(inverted_index)
#         self.__a = a

#     def _first_starting_at_or_after(self, k):
#         u,v = self.__a._first_starting_at_or_after(k)
#         return (u,u)


#     def _first_ending_at_or_after(self, k):
#         u,v = self.__a._first_ending_at_or_after(k)
#         return (u,u)


#     def _last_ending_at_or_before(self, k):
#         u,v = self.__a._last_ending_at_or_before(k)
#         return (u,u)


#     def _last_starting_at_or_before(self, k):
#         u,v = self.__a._last_starting_at_or_before(k)
#         return (u,u)


# class EndOperator(GCListGenerator):

#     def __init__(self, inverted_index, a):
#         super(EndOperator, self).__init__(inverted_index)
#         self.__a = a

#     def _first_starting_at_or_after(self, k):
#         u,v = self.__a._first_starting_at_or_after(k)
#         return (v,v)


#     def _first_ending_at_or_after(self, k):
#         u,v = self.__a._first_ending_at_or_after(k)
#         return (v,v)


#     def _last_ending_at_or_before(self, k):
#         u,v = self.__a._last_ending_at_or_before(k)
#         return (v,v)


#     def _last_starting_at_or_before(self, k):
#         u,v = self.__a._last_starting_at_or_before(k)
#         return (v,v)


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
