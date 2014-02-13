pyra - Python Region Algebra
============================


Pyra is a python implementation of the region algebra and query language described in [1]. 
Region algebras are used to efficiently query semi-structured text documents. This particular
region algebra operates on Generalized Concordance Lists (GCLs). GCLs are lists of regions
(a.k.a., extents), which obey the following constraint: *No region in the list may have another
region from the same lists nested within it*. For a quick online introduction to this region
algebra, and why it is useful, visit:

[Wumpus Search](http://www.wumpus-search.org/docs/gcl.html) 

In general, this region algebra is good for extracting data from documents that have lightweight
structure, and is an alternative to more heavyweight solutions like XPath queries.


### Algebra and Query Language

Our region algebra consists of the following elements:

(Essentially identical to the conventions used in Wumpus [See above])

    Elementary Types
    —---------------
    "token"             Tokens are quoted strings. Use \" to escape quotes, and \\ to escape escapes
    "a", "b", "c"       Phrases are comma separated tokens
    INT                 Positions are indicated as bare integers (e.g., 4071)

    Operators (here A and B are arbitrary region algebra expressions, N is an integer)
    ----------------------------------------------------------------------------------
    A ^ B               Returns all extents that match both A and B
    A + B               Returns all extents that match either A or B (or both)
    A .. B              Returns all extents that start with A and end with B
    A > B               Returns all extents that match A and contain an extent matching B 
    A < B               Returns all extents that match A, contained in an extent matching B

    _{A}                The 'start' projection. For each extent (u,v) in A, return (u,u)
    {A}_                The 'end' projection. For each extent (u,v) in A, return (v,v)

    [N]                 Returns all extents of length N, where N is an integer (basically a sliding window)

    Not yet implemented:
    A /> B              Returns all extents that match A but do not contain an extent matching B
    A /< B              Returns all extents that match A, not contained in an extent matching B


### Examples

Suppose we an XML document containing the complete works of Shakespeare (see './pyra/examples').
We can then run the following queries using pyra:

**Return the titles of all plays, acts, scenes, etc.**

    "<title>".."</title>"         

    Results:
    slice(15,23):               <title> the tragedy of antony and cleopatra </title>
    slice(68,72):               <title> dramatis personae </title>
    slice(279,283):             <title> act i </title>
    slice(284,295):             <title> scene i alexandria a room in cleopatra s palace </title>
    slice(1097,1105):           <title> scene ii the same another room </title>
    slice(3526,3534):           <title> scene iii the same another room </title>
    slice(4889,4898):           <title> scene iv rome octavius caesar s house </title>
    slice(5885,5893):           <title> scene v alexandria cleopatra s palace </title>

    ... And, many more ...

 
**Return the titles of all plays**
**(i.e., the first title found in the play)**

    ("<title>".."</title>") < ("<play>".."</title>")         

    Results:
    slice(15,23):                <title> the tragedy of antony and cleopatra </title>
    slice(40514,40522):          <title> all s well that ends well </title>
    slice(75567,75573):          <title> as you like it </title>
    slice(107909,107915):        <title> the comedy of errors </title>
    slice(130779,130785):        <title> the tragedy of coriolanus </title>
    slice(173424,173427):        <title> cymbeline </title>
    slice(214962,214969):        <title> a midsummer night s dream </title>
    slice(239304,239313):        <title> the tragedy of hamlet prince of denmark </title>

    ... And, many more ...


**Return the titles of all plays containing the word 'henry'**

    (("<title>".."</title>") < ("<play>".."</title>")) > "henry"  

    Results:
    slice(322005,322014):        <title> the second part of henry the fourth </title>
    slice(361126,361134):        <title> the life of henry the fifth </title>
    slice(399220,399229):        <title> the first part of henry the sixth </title>
    slice(431541,431550):        <title> the second part of henry the sixth </title>
    slice(469240,469249):        <title> the third part of henry the sixth </title>
    slice(505920,505932):        <title> the famous history of the life of henry the ei...


**Return short play titles (4 or few words)**
**(Note: We have to include the tags in the token count)**

    (("<title>".."</title>") < ("<play>".."</title>")) < [6] 

    Results:
    slice(75567,75573):          <title> as you like it </title>
    slice(107909,107915):        <title> the comedy of errors </title>
    slice(130779,130785):        <title> the tragedy of coriolanus </title>
    slice(173424,173427):        <title> cymbeline </title>
    slice(677133,677138):        <title> measure for measure </title>
    slice(744759,744765):        <title> the tragedy of macbeth </title>
    slice(771553,771559):        <title> the merchant of venice </title>
    slice(802540,802546):        <title> much ado about nothing </title>
    slice(875994,876000):        <title> pericles prince of tyre </title>
    slice(1081750,1081754):      <title> the tempest </title>
    slice(1233968,1233974):      <title> the winter s tale </title>


**Return the title of all plays containing the phrase 'to be or not to be'**

    (("<title>".."</title>") < ("<play>".."</title>")) < (("<play>".."</play>") > ("to", "be", "or", "not", "to", "be"))

    Results:
    slice(239304,239313):        <title> the tragedy of hamlet prince of denmark </title>

### Code Examples

So how do you actually write code that uses or calls *pyra*?

Here's an example implementation of the above queries:

        from pyra import InvertedIndex, GCL

        # See examples/gcl_shell.py for an example describing how to get
        # a tokenized corpus for Shakespeare

        iindex  = InvertedIndex(tokens)
        gcl     = GCL(iidx)  

        # Print titles of acts, plays, scenes, etc
        for myslice in g.parse('"<title>".."</title>"'):
            print("%s \t %s", (str(myslice), " ".join(corpus[myslice]))


        # Print titles of plays
        play_titles = g.parse('("<title>".."</title>") < ("<play>".."</title>")')

        for myslice in play_titles:
            print("%s \t %s", (str(myslice), " ".join(corpus[myslice]))

        
        # Return the titles of plays containing the word 'henry'
        #
        # Use parameterization to reuse the last expression
        # (Makes for readable code, and may benefit from results caching
        # if I ever get around to implementing it)

        for myslice in g.parse('%1 > "henry"', play_titles):
            print("%s \t %s", (str(myslice), " ".join(corpus[myslice]))
      

        # Return the titles of plays, where the plays mention a
        # 'witch' and 'duncan' 

        whole_plays = g.parse("<play>..</play>")
        for myslice in g.parse('%1 < (%2 > ("witch" ^ "duncan"))', play_titles, whole_plays):
            print("%s \t %s", (str(myslice), " ".join(corpus[myslice]))


### Ply Grammar

This package uses ply python module to parse the GCL expressions.
Here is a simplified sketch of the grammar pyra uses:

    gcl_expr :  ( gcl_expr )            |
                gcl_expr ... gcl_expr   |
                gcl_expr > gcl_expr     |
                gcl_expr < gcl_expr     |
                [ INT ]                 |
                INT                     |
                phrase

    phrase : STRING , phrase  |
             STRING

### References

[1]  Clarke, C. L., Cormack, G. V., & Burkowski, F. J. (1995). An algebra for structured text search
     and a framework for its implementation. The Computer Journal, 38(1), 43-56. Chicago
