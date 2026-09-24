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

### Installation

Requires Python 3.11 or newer, including Python 3.14. From a checkout:

```sh
python3 -m venv .venv
. .venv/bin/activate
python -m pip install .
```

Installation includes PLY 3.11 for parsing query strings. The existing query
language and Python API are unchanged.

Run the interactive Shakespeare example or the tests from the repository root:

```sh
python examples/gcl_shell.py
python -m unittest discover -s test -v
```

For development, use `python -m pip install -e .` instead.

GitHub Actions runs the suite on Python 3.11, 3.12, 3.13, and 3.14 for every
pull request and push to `master`. CI installs the package with uv and runs the
tests in isolated mode (`python -I`) to exercise the installed library.


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
    A /> B              Returns all extents that match A but do not contain an extent matching B
    A /< B              Returns all extents that match A, not contained in an extent matching B

    _{A}                The 'start' projection. For each extent (u,v) in A, return (u,u)
    {A}_                The 'end' projection. For each extent (u,v) in A, return (v,v)

    [N]                 Returns all extents of length N, where N is an integer (basically a sliding window)

### Examples

Suppose we have an XML document containing the complete works of Shakespeare (see './examples').
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

```python
from pyra import InvertedIndex, GCL

# Replace this sample with tokenized Shakespeare text; see examples/gcl_shell.py.
corpus = "<play> <title> macbeth </title> witch duncan </play>".split()
gcl = GCL(InvertedIndex(corpus))

# Print titles of acts, plays, scenes, etc.
for region in gcl.parse('"<title>".."</title>"'):
    print(f"{region}\t{' '.join(corpus[region])}")

# Print titles of plays.
play_titles = gcl.parse('("<title>".."</title>") < ("<play>".."</title>")')
for region in play_titles:
    print(f"{region}\t{' '.join(corpus[region])}")

# Use parameterization to reuse an expression.
for region in gcl.parse('%1 > "henry"', play_titles):
    print(f"{region}\t{' '.join(corpus[region])}")

# Return the titles of plays mentioning both 'witch' and 'duncan'.
whole_plays = gcl.parse('"<play>".."</play>"')
for region in gcl.parse(
    '%1 < (%2 > ("witch" ^ "duncan"))', play_titles, whole_plays
):
    print(f"{region}\t{' '.join(corpus[region])}")
```

### Source checkpoints

`InvertedIndex` accepts an iterable of plain terms or `(term, source_offset)`
pairs, where `term` is a string and `source_offset` is an integer. Construction
consumes the iterable once, so generators work. Do not mix the two input forms.

```python
index = InvertedIndex([("hello", 100), ("world", 120), ("hello", 170)])
assert list(index.postings("hello")) == [0, 2]
assert index.checkpoint(0) == (0, 100)

plain = InvertedIndex("hello world hello".split())
assert plain.checkpoint(2) == (2, 2)
```

`checkpoint(position)` returns the nearest retained checkpoint at or before the
requested token position as `(checkpoint_token_position, source_offset)`.
Plain terms use an implicit identity mapping with no checkpoint entries.
Explicit offsets are sampled sparsely; checkpoint spacing is an implementation
detail. Postings and query results always use token coordinates.

Source offsets are opaque, nondecreasing integers: they may be bytes, characters,
or another source-defined coordinate. Equal, negative, and arbitrarily large
offsets are allowed; booleans are not. The source and its reader are responsible
for agreeing on how to resume from a checkpoint. Lookup does not access the
source or reconstruct text.

Positions from zero through `corpus_length` are accepted. At `corpus_length`, an
explicit-offset index returns its last checkpoint, not an inferred EOF offset.
An empty index returns `(0, 0)` for `checkpoint(0)`. Invalid position types raise
`TypeError`; out-of-range positions raise `IndexError`.

Other hashable plain terms remain supported, except that two-element tuples
beginning with a string are reserved for the source-offset form.

### Ply Grammar

This package uses ply python module to parse the GCL expressions.
Here is a simplified sketch of the grammar pyra uses:

    gcl_expr :  ( gcl_expr )            |
                gcl_expr ... gcl_expr   |
                gcl_expr > gcl_expr     |
                gcl_expr < gcl_expr     |
                gcl_expr /> gcl_expr    |
                gcl_expr /< gcl_expr    |
                [ INT ]                 |
                INT                     |
                phrase

    phrase : STRING , phrase  |
             STRING

### Passage Ranking

The passage-ranking implementation in `pyra/icover.py` uses the i-cover generation
algorithm and logarithmic term-frequency and passage-length scoring described in
[2] and [3]. For a fuller account of passage retrieval and answer extraction in
the MultiText question-answering system, see [4].

### References

[1]  Clarke, C. L., Cormack, G. V., & Burkowski, F. J. (1995). An algebra for structured text search
     and a framework for its implementation. The Computer Journal, 38(1), 43-56. Chicago

[2]  Clarke, C. L. A., & Terra, E. L. (2004).
     [Approximating the Top-m Passages in a Parallel Question Answering System](https://doi.org/10.1145/1031171.1031259).
     Proceedings of CIKM 2004, 454-462.
     [PDF](https://plg.uwaterloo.ca/~claclark/top.pdf).
     Section 3 includes the passage-scoring formula (Equation 1) and i-cover generation algorithm (Figure 3).

[3]  Clarke, C. L. A., Cormack, G. V., & Lynam, T. R. (2001).
     [Exploiting Redundancy in Question Answering](https://doi.org/10.1145/383952.384024).
     Proceedings of SIGIR 2001, 358-365.
     [Author's PostScript version](https://plg.uwaterloo.ca/~claclark/sigir01.ps).
     Section 2 describes the passage-scoring model and i-covers.

[4]  Clarke, C. L. A., Cormack, G. V., Lynam, T. R., & Terra, E. L. (2006).
     [Question Answering by Passage Selection](https://doi.org/10.1007/978-1-4020-4746-6_8).
     In T. Strzalkowski & S. Harabagiu (Eds.), Advances in Open Domain Question Answering,
     259-283. Springer.
