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

### Interactive CLI

Run `pyra <filename>` (or `python -m pyra <filename>`) to index a UTF-8 text file
and open an interactive prompt:

```text
$ pyra notes.txt
Indexing notes.txt...
Pyra — notes.txt · 1,234 tokens

Enter a GCL expression, or ? search terms for ranked passages.
Ctrl-C cancels; Ctrl-D (Windows: Ctrl-Z then Enter) exits.

pyra> "<title>".."</title>"
```

Output:

```text
1. [15:23] <TITLE>The Tragedy of Antony and Cleopatra</TITLE>
2. [68:72] <TITLE>Dramatis Personae</TITLE>
3. [279:283] <TITLE>ACT I</TITLE>
4. [284:295] <TITLE>SCENE I. Alexandria. A room in CLEOPATRA's palace.</TITLE>
5. [1096:1104] <TITLE>SCENE II. The same. Another room.</TITLE>
6. [3525:3533] <TITLE>SCENE III. The same. Another room.</TITLE>
7. [4888:4897] <TITLE>SCENE IV. Rome. OCTAVIUS CAESAR's house.</TITLE>
8. [5883:5891] <TITLE>SCENE V. Alexandria. CLEOPATRA's palace.</TITLE>
9. [6866:6870] <TITLE>ACT II</TITLE>
10. [6871:6879] <TITLE>SCENE I. Messina. POMPEY's house.</TITLE>
Space: more · Any other key: back to query
```

For passage ranking, enter `?` followed by search terms. For example:

```text
pyra> ? to be or not
```

Output:

<pre>
1. [258812:258816] Enter HAMLET</STAGEDIR> <SPEECH> <SPEAKER>HAMLET</SPEAKER> <LINE><b>To be, or not</b> to be: that is the question:</LINE> <LINE>
2. [258813:258817] HAMLET</STAGEDIR> <SPEECH> <SPEAKER>HAMLET</SPEAKER> <LINE>To <b>be, or not to</b> be: that is the question:</LINE> <LINE>Whether
3. [258814:258818] </STAGEDIR> <SPEECH> <SPEAKER>HAMLET</SPEAKER> <LINE>To be, <b>or not to be<b/>: that is the question:</LINE> <LINE>Whether 'tis
4. [1254792:1254797] play on;</LINE> <LINE>Not like a corse; <b>or if, not to be</b> buried,</LINE> <LINE>But quick and in mine
5. [81769:81772] </LINE> <LINE>If that I do not dream <b>or be not</b> frantic,--</LINE> <LINE>As I do trust I
6. [258813:258816] HAMLET</STAGEDIR> <SPEECH> <SPEAKER>HAMLET</SPEAKER> <LINE>To <b>be, or not</b> to be: that is the question:</LINE> <LINE>
7. [1104261:1104264] GONZALO</SPEAKER> <LINE>Whether this be</LINE> <LINE><b>Or be not</b>, I'll not swear.</LINE> </SPEECH> <SPEECH> <SPEAKER>
8. [648327:648334] three ages since: but I think now 'tis <b>not to be</LINE> <LINE>found; or</b>, if it were, it would neither serve for
9. [141750:141753] to stuff a botcher's</LINE> <LINE>cushion, <b>or to be</b> entombed in an ass's pack-</LINE> <LINE>
10. [258812:258815] Enter HAMLET</STAGEDIR> <SPEECH> <SPEAKER>HAMLET</SPEAKER> <LINE><b>To be, or</b> not to be: that is the question:</LINE>
</pre>

Queries beginning with `? ` retrieve passages ranked by cover density; other
queries are GCL expressions, returned in document order.

Results display the original text with whitespace collapsed, numbered alongside
exclusive-stop token ranges `[start:stop]`. Ranked results include up to eight
surrounding tokens on each side for context; the range still identifies the
match. In a color terminal, the matched slice has a yellow background, leaving
the surrounding context unhighlighted. Redirected output stays plain; set
`NO_COLOR=1` to disable highlighting in the terminal.

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
XML corpus, preserving tags as tokens. It prints the example queries below, then
uses the same interactive shell as `pyra`. With that tokenization, we can run the
following queries using Pyra:

**Return the titles of all plays, acts, scenes, etc.**

    "<title>".."</title>"         

    Results:
    slice(15,23):               <TITLE>The Tragedy of Antony and Cleopatra</TITLE>
    slice(68,72):               <TITLE>Dramatis Personae</TITLE>
    slice(279,283):             <TITLE>ACT I</TITLE>
    slice(284,295):             <TITLE>SCENE I. Alexandria. A room in CLEOPATRA's palace.</TITLE>
    slice(1096,1104):           <TITLE>SCENE II. The same. Another room.</TITLE>
    slice(3525,3533):           <TITLE>SCENE III. The same. Another room.</TITLE>
    slice(4888,4897):           <TITLE>SCENE IV. Rome. OCTAVIUS CAESAR's house.</TITLE>
    slice(5883,5891):           <TITLE>SCENE V. Alexandria. CLEOPATRA's palace.</TITLE>

    ... And, many more ...


**Return the titles of all plays**
**(i.e., the first title found in the play)**

    ("<title>".."</title>") < ("<play>".."</title>")         

    Results:
    slice(15,23):               <TITLE>The Tragedy of Antony and Cleopatra</TITLE>
    slice(40499,40507):         <TITLE>All's Well That Ends Well</TITLE>
    slice(75547,75553):         <TITLE>As You Like It</TITLE>
    slice(107885,107891):       <TITLE>The Comedy of Errors</TITLE>
    slice(130751,130757):       <TITLE>The Tragedy of Coriolanus</TITLE>
    slice(173376,173379):       <TITLE>Cymbeline</TITLE>
    slice(214898,214905):       <TITLE>A Midsummer Night's Dream</TITLE>
    slice(239237,239246):       <TITLE>The Tragedy of Hamlet, Prince of Denmark</TITLE>

    ... And, many more ...


**Return all play titles containing the word 'henry'**

    (("<title>".."</title>") < ("<play>".."</title>")) > "henry"  

    Results:
    slice(285527,285536):       <TITLE>The First Part of Henry the Fourth</TITLE>
    slice(321918,321927):       <TITLE>The Second Part of Henry the Fourth</TITLE>
    slice(361010,361018):       <TITLE>The Life of Henry the Fifth</TITLE>
    slice(399096,399105):       <TITLE>The First Part of Henry the Sixth</TITLE>
    slice(431400,431409):       <TITLE>The Second Part of Henry the Sixth</TITLE>
    slice(469082,469091):       <TITLE>The Third Part of Henry the Sixth</TITLE>
    slice(505742,505754):       <TITLE>The Famous History of the Life of Henry the Eighth</TITLE>


**Return short play titles (4 or fewer words)**
**(Note: We have to include the tags in the token count)**

    (("<title>".."</title>") < ("<play>".."</title>")) < [6] 

    Results:
    slice(75547,75553):         <TITLE>As You Like It</TITLE>
    slice(107885,107891):       <TITLE>The Comedy of Errors</TITLE>
    slice(130751,130757):       <TITLE>The Tragedy of Coriolanus</TITLE>
    slice(173376,173379):       <TITLE>Cymbeline</TITLE>
    slice(676893,676898):       <TITLE>Measure for Measure</TITLE>
    slice(744508,744514):       <TITLE>The Tragedy of Macbeth</TITLE>
    slice(771291,771297):       <TITLE>The Merchant of Venice</TITLE>
    slice(802276,802282):       <TITLE>Much Ado about Nothing</TITLE>
    slice(875723,875729):       <TITLE>Pericles, Prince of Tyre</TITLE>
    slice(1081436,1081440):     <TITLE>The Tempest</TITLE>
    slice(1233608,1233614):     <TITLE>The Winter's Tale</TITLE>


**Return the titles of all plays containing the phrase 'to be or not to be'**

    (("<title>".."</title>") < ("<play>".."</title>")) < (("<play>".."</play>") > ("to", "be", "or", "not", "to", "be"))

    Results:
    slice(239237,239246):       <TITLE>The Tragedy of Hamlet, Prince of Denmark</TITLE>


### Code Examples

First, we need a source of tokens for our corpus. The simplest is a string,
but we can also use a UTF-8 text file.

```python
from pyra import GCL, FileTextSource, InvertedIndex, StringTextSource

string_source = StringTextSource("The brown, FOX sleeps. Another brown fox runs.")
file_source = FileTextSource("notes.txt")  # Alternative: supply your own UTF-8 file.
```

Both sources use `RegexTokenizer` by default: it lowercases terms and preserves
simple XML tags using the same splitting rules as the CLI and Shakespeare demo.
Empty fragments are omitted. To use word-only, case-folded tokenization instead,
pass `tokenizer=RegexTokenizer(r"\w+", normalize=str.casefold)` to either source.
Each iteration yields fresh `(term, source_offset)` pairs;
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
at token zero (the actual implementation currently uses a stride of 256). Given this input:

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
