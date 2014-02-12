pyra - Python Region Algebra
============================


Pyra is a python implementation of the region algebra and query language described in [1]. 
Region algebras are used to efficiently query semi-structured text documents. For a quick
online introduction to this region algebra, and why it is useful, visit:

[Wumpus Search Docs](http://www.wumpus-search.org/docs/gcl.html). 

In general, region algebras are good for extracting data from documents that have lightweight structure 
(semi-structured), and are an alternative to more heavyweight solutions like XPath queries.


Algebra and Query Language
===========================

Our region algebra consists of the following elements:
(Essentially identical to the conventions used in Wumpus [See above])

    Elementary Types
    —---------------
    "token"             Tokens are quoted strings. Use \" to escape quotes, and \\ to escape escapes
    "a", "b", "c"       Phrases are comma separated tokens
    INT                 Positions are indicated as bare integers (e.g., 4071)
    [INT]               Lengths are indicated as integers inside square brackets     

    Operators (here A and B are arbitrary region algebra expressions)
    -----------------------------------------------------------------
    A .. B              Extent that starts with A and ends with B
    A > B               Extent A contains extent B 
    A < B               Extent A contain is contained in extent B 

    More operators will be implemented in the future. With these 3, we can do a lot (see below)


Examples
========

Suppose we have indexed the complete works of Shakespeare, as an XML-like document. We can then 
run the following queries using pyra:


Return the titles of all plays, acts, scenes, etc.

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

 
Return the titles of all plays
(i.e., the first title found in the play)

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


Return the titles of all plays containing the word 'henry'

    (("<title>".."</title>") < ("<play>".."</title>")) > "henry"  

    Results:
    slice(322005,322014):        <title> the second part of henry the fourth </title>
    slice(361126,361134):        <title> the life of henry the fifth </title>
    slice(399220,399229):        <title> the first part of henry the sixth </title>
    slice(431541,431550):        <title> the second part of henry the sixth </title>
    slice(469240,469249):        <title> the third part of henry the sixth </title>
    slice(505920,505932):        <title> the famous history of the life of henry the ei...

  
Return short play titles (4 or few words)
(Note: We have to include the tags in the token count)

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


Return the title of all plays containing the phrase 'to be or not to be'

    (("<title>".."</title>") < ("<play>".."</title>")) < (("<play>".."</play>") > ("to", "be", "or", "not", "to", "be"))

    Results:
    slice(239304,239313):        <title> the tragedy of hamlet prince of denmark </title>


Ply Grammar
===========
This package uses ply python module to parse the GCL expressions.
Here is a simplified sketch of the grammar pyra uses:

    gcl_expr :  ( gcl_expr )            |
                gcl_expr ... gcl_expr   |
                gcl_expr > gcl_expr     |
                gcl_expr < gcl_expr'    |
                [ INT ]                 |
                INT                     |
                phrase

    phrase : STRING , phrase  |
             STRING

References
==========

[1]  Clarke, C. L., Cormack, G. V., & Burkowski, F. J. (1995). An algebra for structured text search
     and a framework for its implementation. The Computer Journal, 38(1), 43-56. Chicago
