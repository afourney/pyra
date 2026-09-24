pyra - Python Region Algebra
============================


Pyra is a Python implementation of the region algebra and query language described in [1].
Region algebras are used to efficiently query semi-structured text documents. This particular
region algebra operates on Generalized Concordance Lists (GCLs). GCLs are lists of regions
(a.k.a., extents), which obey the following constraint: *No region in the list may have another
region from the same list nested within it*. For a quick online introduction to this region
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

Installation includes PLY 3.11 for parsing query strings.

Run the interactive Shakespeare example or the tests from the repository root:

```sh
python examples/gcl_shell.py
python -m unittest discover -s test -v
```

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

The interactive example in `examples/gcl_shell.py` tokenizes the bundled Shakespeare
XML corpus, preserving tags as tokens. With that tokenization, we can run the
following queries using Pyra:

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


**Return all play titles containing the word 'henry'**

    (("<title>".."</title>") < ("<play>".."</title>")) > "henry"  

    Results:
    slice(322005,322014):        <title> the second part of henry the fourth </title>
    slice(361126,361134):        <title> the life of henry the fifth </title>
    slice(399220,399229):        <title> the first part of henry the sixth </title>
    slice(431541,431550):        <title> the second part of henry the sixth </title>
    slice(469240,469249):        <title> the third part of henry the sixth </title>
    slice(505920,505932):        <title> the famous history of the life of henry the ei...


**Return short play titles (4 or fewer words)**
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


**Return the titles of all plays containing the phrase 'to be or not to be'**

    (("<title>".."</title>") < ("<play>".."</title>")) < (("<play>".."</play>") > ("to", "be", "or", "not", "to", "be"))

    Results:
    slice(239304,239313):        <title> the tragedy of hamlet prince of denmark </title>

### Code Examples

First, we need a source of tokens for our corpus. The simplest is a string,
but we can also use a UTF-8 text file.

```python
from pyra import GCL, FileTextSource, InvertedIndex, StringTextSource

string_source = StringTextSource("The brown, FOX sleeps. Another brown fox runs.")
file_source = FileTextSource("notes.txt")  # Alternative: supply your own UTF-8 file.
```

Both sources use `RegexTokenizer` by default: it matches Unicode `\w+` terms
and case-folds them. Unlike the Shakespeare example's tokenizer, it does not
preserve XML tags. Each iteration yields fresh `(term, source_offset)` pairs;
string offsets count characters, while file offsets count bytes.

Next, we need to build an index from the source.

```python
index = InvertedIndex(string_source)
```

Finally, we can bind a reader from the source to the index to retrieve regions
of text that match a query. For example, to find the phrase "brown fox":

```python
reader = string_source.reader(index)
for region in GCL(index).parse('"brown", "fox"'):
    print(reader[region])  # "brown, FOX", then "brown fox"
```

Reader slices use token positions with exclusive stops, matching GCL results.
They preserve the original text between the first token's start and the last
token's end, including intervening punctuation and whitespace. Negative and
omitted bounds and clipping follow Python slicing; empty slices return `""`.
Only slices with a step of `1` are supported, not integer indexing.

Always bind a reader to an index built from that source's positioned tokens.
Keep the source contents and tokenizer configuration unchanged while using
the index; rebuild after changes. There is no automatic stale-index detection.

### Cover-density ranking

Pyra can also rank passages by cover density. The passage-ranking implementation
in `pyra/icover.py` uses the i-cover generation algorithm and logarithmic term-frequency
and passage-length scoring described in [2] and [3]. For a fuller account of passage
retrieval and answer extraction in the MultiText question-answering system, see [4].

Like GCL, cover-density ranking produces exclusive-stop token slices that can
be used with the reader above. `rank()` returns `(slice, score)` pairs in
descending score order:

```python
from pyra import CoverDensityRanking

for region, score in CoverDensityRanking(index).rank(["brown", "fox"]):
    print(score, reader[region])
```

For unranked covers, `iCovers(i, query)` yields dictionaries with `"slice"` and
`"terms"` fields. The `"slice"` field replaces the earlier inclusive `"extent"`
tuple: use `reader[cover["slice"]]` or `tokens[cover["slice"]]` rather than
`tokens[start:end + 1]`.

### Index checkpoints

The index deals with tokens, but downstream users likely want to retrieve original passages
without normalizing or otherwise altering the original text. `InvertedIndex` supports
token offset checkpointing. When building an index, `InvertedIndex` accepts an iterable
of plain terms or `(term, source_offset)` pairs, where `term` is a string and `source_offset`
is an integer such as the term's character offset in a string, or byte offset in a file.
These offsets are used to support checkpointing, which facilitates efficient passage retrieval
later. Specifically, `checkpoint(position)` returns the nearest retained checkpoint at or
before the requested token position as `(checkpoint_token_position, source_offset)`.

For illustration, suppose checkpoints are retained every three tokens, starting
at token zero. The implementation currently uses a stride of 256; the smaller
stride here keeps the example short. Given this input:

```python
checkpoint_index = InvertedIndex(
    [("hello", 100), ("world", 120), ("hello", 170), ("world", 210)]
)
```

With the illustrative three-token stride, the results would be:

| Call | Result |
| --- | --- |
| `checkpoint_index.checkpoint(0)` | `(0, 100)` |
| `checkpoint_index.checkpoint(1)` | `(0, 100)` |
| `checkpoint_index.checkpoint(2)` | `(0, 100)` |
| `checkpoint_index.checkpoint(3)` | `(3, 210)` |

In this example, the second and third tokens (indices 1 and 2) *start* somewhere between
offsets 100 and 209 inclusive. The fourth token starts at offset 210. To retrieve
the source substring containing the second and third tokens, one would begin
tokenizing from offset 100, skip the first token, then retain the substring from
the start of the second token through the end of the third. For this example,
using character offsets and the original token text, that substring would be
`source[120:175]`.

This is how `StringTextSource` and `FileTextSource` retrieve passages.
Calling `source.reader(index)` returns a `PassageReader` that maps token slices
to the original source text using the checkpointing mechanism described above.

Source offsets must be nondecreasing integers, and plain terms and positioned
tokens cannot be mixed in one index. For plain terms, `checkpoint(position)`
returns `(position, position)` without storing checkpoints.

### PLY Grammar

This package uses the PLY Python module to parse GCL expressions.
Here is a simplified sketch of the grammar Pyra uses:

    gcl_expr :  ( gcl_expr )            |
                gcl_expr .. gcl_expr    |
                gcl_expr ^ gcl_expr     |
                gcl_expr + gcl_expr     |
                gcl_expr > gcl_expr     |
                gcl_expr < gcl_expr     |
                gcl_expr /> gcl_expr    |
                gcl_expr /< gcl_expr    |
                _{ gcl_expr }           |
                { gcl_expr }_           |
                [ INT ]                 |
                INT                     |
                phrase

    phrase : STRING , phrase  |
             STRING

### Development

Install the development tools with [uv](https://docs.astral.sh/uv/):

```sh
uv sync --locked
uv run poe lint        # Check Ruff lint rules
uv run poe format-fix  # Apply Ruff formatting
uv run poe test        # Run the unittest suite
uv run poe typecheck   # Run strict Pyright checks
uv run poe check-all   # Check formatting, lint, spelling, types, and tests
```

GitHub Actions runs the suite on Python 3.11, 3.12, 3.13, and 3.14 for every
pull request and push to `master`. CI runs `poe check-all` after installing the
package with uv in non-editable mode.

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
