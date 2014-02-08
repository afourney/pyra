#!/usr/bin/python
import operators

# Conventions used in this file:
# #####################################################
#
# fsaoa == First interval starting at or after k (tau)
# feaoa == First interval ending at or after k (rho)
# leaob == Last interval ending at or before k (tau prime)
# lsaob == Last interval starting at or before k (rho prime)
#
#  NOTE:: To match the textbook and paper, all private methods
#         operate on and return closed intervals (represented
#         as tuples). ALL PUBLIC METHODS take and return
#         python slices, which are intervals closed on the left
#         and open on the right. 
#

INF = float('inf')


class QueryProcessor(object):

    def __init__(self, inverted_index):
        self.__idx = inverted_index


    @property
    def index(self):
        return self.__idx


    def list(self, gcl_query, limit=INF):
        results = [] 

        k = float(0)
        while k < INF:
            u,v = self.__gcl_fsaoa(gcl_query, k)
            if u != INF:
                results.append(extent2slice( (u,v) ))
                if len(results) >= limit:
                    break
            k = u + 1

        return results


    def count(self, gcl_query):
        c = 0

        e = self.first(gcl_query)
        while e.begin < INF:
            c += 1
            e = self.next(gcl_query, e.begin)
                
        return c       


    # BELOW THERE BE DRAGONS
    ##########################################################################


    def __gcl_fsaoa(self, query, k):
        operator = query[0]
        operands = query[1::]

        if k == INF:
            return (INF,INF)
        elif k == -INF:
            return (-INF,-INF)

        if operator == operators._GC_LIST:
            return self.__gcl_fsaoa_gclist(operands, k)
        elif operator == operators._PHRASE:
            return self.__gcl_fsaoa_phrase(operands, k)
        elif operator == operators._BOUNDED:
            return self.__gcl_fsaoa_bounded(operands, k)
        elif operator == operators._CONTAINING:
            return self.__gcl_fsaoa_containing(operands, k)
        else:
            raise NotImplementedError()


    def __gcl_feaoa(self, query, k):
        operator = query[0]
        operands = query[1::]

        if k == INF:
            return (INF,INF)
        elif k == -INF:
            return (-INF,-INF)

        if operator == operators._GC_LIST:
            return self.__gcl_feaoa_gclist(operands, k)
        elif operator == operators._PHRASE:
            return self.__gcl_feaoa_phrase(operands, k)
        elif operator == operators._BOUNDED:
            return self.__gcl_feaoa_bounded(operands, k)
        elif operator == operators._CONTAINING:
            return self.__gcl_feaoa_containing(operands, k)
        else:
            raise NotImplementedError()


    def __gcl_leab(self, query, k):
        operator = query[0]
        operands = query[1::]

        if k == INF:
            return (INF,INF)
        elif k == -INF:
            return (-INF,-INF)

        if operator == operators._GC_LIST:
            return self.__gcl_leab_gclist(operands, k)
        elif operator == operators._PHRASE:
            return self.__gcl_leab_phrase(operands, k)
        elif operator == operators._BOUNDED:
            return self.__gcl_leab_bounded(operands, k)
        elif operator == operators._CONTAINING:
            return self.__gcl_leab_containing(operands, k)
        else:
            raise NotImplementedError()


    def __gcl_lsaob(self, query, k):
        operator = query[0]
        operands = query[1::]

        if k == INF:
            return (INF,INF)
        elif k == -INF:
            return (-INF,-INF)

        if operator == operators._GC_LIST:
            return self.__gcl_lsaob_gclist(operands, k)
        elif operator == operators._PHRASE:
            return self.__gcl_lsaob_phrase(operands, k)
        elif operator == operators._BOUNDED:
            return self.__gcl_lsaob_bounded(operands, k)
        elif operator == operators._CONTAINING:
            return self.__gcl_lsaob_containing(operands, k)
        else:
            raise NotImplementedError()


    ##########################################################################


    #
    # GC_LISTS
    #

    def __gcl_fsaoa_gclist(self, operands, k):
        # First interval starting at or after k
        # TODO: Use binary search
        for i in range(0, len(operands)):
            if operands[i][0] >= k:
                return operands[i]
        return (INF,INF)


    def __gcl_feaoa_gclist(self, operands, k):
        # First interval ending at or after k
        # TODO: Use binary search
        for i in range(0, len(operands)):
            if operands[i][1] >= k:
                return operands[i]
        return (INF,INF)


    def __gcl_leab_gclist(self, operands, k):
        # Last interval ending at or before k
        # TODO: Use binary search
        for i in range(len(operands)-1,-1,-1):
            if operands[i][1] <= k:
                return operands[i]
        return (-INF,-INF)


    def __gcl_lsaob_gclist(self, operands, k):
        # Last interval starting at or before k
        # TODO: Use binary search
        for i in range(len(operands)-1,-1,-1):
            if operands[i][0] <= k:
                return operands[i]
        return (-INF,-INF)

    #
    # PHRASES
    #
    def __gcl_fsaoa_phrase(self, operands, k):
        # First interval starting at or after k
        if k == 0:
            return self.__next_phrase(operands,-INF)
        else:
            return self.__next_phrase(operands,k-1)


    def __gcl_feaoa_phrase(self, operands, k):
        # First interval ending at or after k
        return self.__next_phrase(operands, k - len(operands))


    def __gcl_leab_phrase(self, operands, k):
        # Last interval ending at or before k
        return self.__prev_phrase(operands, k - len(operands) + 2)


    def __gcl_lsaob_phrase(self, operands, k):
        # Last interval starting at or before k
        return self.__prev_phrase(operands,k+1)


    # Helper methods for phrases (TODO: Consider eliminating)
    def __next_phrase(self, tokens, position):
        v = position
        for i in range(0, len(tokens)):
            v = self.__idx.next(tokens[i], v)
        if v == INF:
            return (INF, INF)
        u = v
        for i in range(len(tokens)-2,-1,-1):
            u = self.__idx.prev(tokens[i], u)
        if v-u == len(tokens)-1:
            return (u,v)
        else:
            return self.__next_phrase(tokens, u)


    def __prev_phrase(self, tokens, position):
        v = position
        for i in range(len(tokens)-1,-1,-1):
            v = self.__idx.prev(tokens[i], v)
        if v == -INF:
            return (-INF, -INF)
        u = v
        for i in range(1,len(tokens)):
            u = self.__idx.next(tokens[i], u)
        if u-v == len(tokens)-1:
            return (v,u)
        else:
            return self.__prev_phrase(tokens, u)


    #
    # BOUNDED
    #
    def __gcl_fsaoa_bounded(self, operands, k):
        a,b = operands

        u0,v0 = self.__gcl_fsaoa(a, k)
        if u0 == INF and v0 == INF:
            return (INF,INF)

        u1,v1 = self.__gcl_fsaoa(b, v0+1)
        if u1 == INF and v1 == INF:
            return (INF,INF)

        u2,v2 = self.__gcl_leab(a, u1-1)
        return (u2,v1)


    def __gcl_feaoa_bounded(self, operands, k):
        a,b = operands

        #1. Skip forwards to find the first interval matching a
        u0,v0 = self.__gcl_feaoa(a, k)
        if u0 == INF and v0 == INF:
            return (INF,INF)

        #2. Skip forward to find the first interval matching b after 1.
        u1,v1 = self.__gcl_fsaoa(b, v0+1)
        if u1 == INF and v1 == INF:
            return (INF,INF)

        #3. Skip backwards to find the last interval matching a ending before 2.
        u2,v2 = self.__gcl_leab(a, u1-1)

        return (u2,v1)


    def __gcl_leab_bounded(self, operands, k):
        raise NotImplementedError()


    def __gcl_lsaob_bounded(self, operands, k):
        raise NotImplementedError()


    #
    # CONTAINING
    #

    def __gcl_fsaoa_containing(self, operands, k):
        # First interval starting at or after k
        a,b = operands

        # Get the first candidate match for A
        u0,v0 = self.__gcl_fsaoa(a, k)
        if u0 == INF and v0 == INF:
            return (INF,INF)

        # Get the first candidate match for B
        u1,v1 = self.__gcl_fsaoa(b, u0)
        if u1 == INF and v1 == INF:
            return (INF,INF)

        # We know u1 >= u0
        # Check containment by verifying that v1 <= v0
        if v1 <= v0:
             return (u0,v0)
        else:
            # Keep looking
            return self.__gcl_fsaoa_containing(operands, v0+1)


    def __gcl_feaoa_containing(self, operands, k):
        # First interval ending at or after k
        a,b = operands

        # Get the first candidate match for A
        u0,v0 = self.__gcl_feaoa(a, k)
        if u0 == INF and v0 == INF:
            return (INF,INF)

        # Get the first candidate match for B
        u1,v1 = self.__gcl_fsaoa(b, u0)
        if u1 == INF and v1 == INF:
            return (INF,INF)

        # We know u1 >= u0
        # Check containment by verifying that v1 <= v0
        if v1 <= v0:
            return (u0,v0)
        else:
            # Keep looking
            return self.__gcl_feaoa_containing(operands, v0+1)


    def __gcl_leab_containing(self, operands, k):
        raise NotImplementedError()


    def __gcl_lsaob_containing(self, operands, k):
        raise NotImplementedError()


#
# Helper method for converting extents to python slices
#

def extent2slice( extent ):
    start = extent[0]
    stop  = extent[1]

    if start == -INF:
        start = None

    if stop == INF:
        stop = None
    else:
        stop += 1

    return slice(start,stop)


