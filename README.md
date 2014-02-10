pyra - Python Region Algebra
============================

Pyra is a python implementation of the region query algebra described in [1]. Region algebras are
used to efficiently query semi-structured text documents. For a quick online introduction to this
region algebra, and why it is useful, visit the [Wumpus Search Docs](http://www.wumpus-search.org/docs/gcl.html). 
In general, region algebras are good for extracting data from documents that have lightweight structure 
(semi-structured), and are an alternative to more heavyweight solutions like XPath queries.


    # Setup the corpus
    corpus  = "the quick brown fox jumps over the lazy dog and the brown dog runs away"
    tokens  = corpus.split()

    # List regions starting with 'brown' and ending with 'dog', containing 
    # the phrase 'fox jumps over'. 

    iidx    = InvertedIndex(tokens)
    g       = GCL(iidx)  

    for s in g.Contains( g.BoundedBy( g.Term('brown'), g.Term('dog') ), g.Phrase('fox', 'jumps', 'over') ):
         print s
         print "'%s'" % (tokens[s],)

The above prints:

    slice(2,9)
    'brown fox jumps over the lazy dog'



References
==========

[1]  Clarke, C. L., Cormack, G. V., & Burkowski, F. J. (1995). An algebra for structured text search
     and a framework for its implementation. The Computer Journal, 38(1), 43-56. Chicago	
