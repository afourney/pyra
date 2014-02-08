# Our operands
_PHRASE             = 'op_phrase'                   # "A", "B", "C"
_LENGTH             = 'op_length'                   # [5] -- all extents of length 5
_GC_LIST            = 'op_gc_list'                  # [(1,10), (17,11)]

# Our operators
_AND                = 'op_and'                      # A and B
_OR                 = 'op_or'                       # A or B    (or both)
_BOUNDED            = 'op_bounded'                  # A .. B    (bounded by A on the left and B on the right)
_CONTAINING         = 'op_containing'               # A > B     (A contains B)
_CONTAINED_IN       = 'op_contained_in'             # A < B     (A is contained in B)
_NOT_CONTAINING     = 'op_not_containing'           # A /> B    (A does not contain B)
_NOT_CONTAINED_IN   = 'op_not_contained_in'         # A /< B    (A is not contained in B)


#
# Main methods for compsing queries
#

def Phrase( *tokens ):
    result = [_PHRASE]
    result.extend(tokens)
    return tuple(result)


def Length( length ):
    return (_LENGTH, length)


def GCList( *extents ):
    # TODO: This should probably take slices...
    result = [_GC_LIST]
    result.extend( [tuple(e[:]) for e in extents] )
    return tuple(result)


def And( a, b ):
    return (_AND, a, b)


def Or( a, b ):
    return (_OR, a, b)


def Bounded( a, b ):
    return (_BOUNDED, a, b)


def Containing( a, b ):
    return (_CONTAINING, a, b)


def ContainedIn( a, b ):
    return (_CONTAINED_IN, a, b)


def NotContaining( a, b ):
    return (_NOT_CONTAINING, a, b)


def NotContainedIn( a, b ):
    return (_NOT_CONTAINED_IN, a, b)


#
# Convenience methods
#

def Term( token ):
    return (_PHRASE, token)

def Position( pos ):
    return (_GC_LIST, tuple(pos, pos)) 

def Extent( ext ):
    return (_GC_LIST, tuple(ext[:])) 
