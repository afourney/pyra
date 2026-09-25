#!/usr/bin/env python3
"""Run a guided search shell over the bundled Shakespeare corpus."""

from __future__ import annotations

import gzip
from pathlib import Path

from pyra import InvertedIndex, RegexTokenizer, StringTextSource
from pyra.cli import run_shell


def main() -> None:
    """Load Shakespeare, print example queries, and start the shared shell."""
    print("Loading Shakespeare XML corpus...")
    corpus_path = Path(__file__).with_name("shakespeare.xml.gz")
    tokenizer = RegexTokenizer()
    with gzip.open(corpus_path, "rt", encoding="utf-8") as stream:
        source = StringTextSource(stream.read(), tokenizer=tokenizer)

    print("Indexing corpus...")
    index = InvertedIndex(source)
    print(f"Done. {index.corpus_length:,} tokens.")

    print("""

Example queries:

    Return the titles of all plays, acts, scenes, etc.

        "<title>".."</title>"

    Return the titles of all plays
    (i.e., the first title found in the play)

        ("<title>".."</title>") < ("<play>".."</title>")

    Return the titles of all plays containing the word 'henry'

        (("<title>".."</title>") < ("<play>".."</title>")) > "henry"

    Return short play titles (3 or few words)
    (Note: We have to include the tags in the token count)

        (("<title>".."</title>") < ("<play>".."</title>")) < [5]

    Return the title of all plays containing the line 'to be or not to be'

        (("<title>".."</title>") < ("<play>".."</title>")) < (("<play>".."</play>") > ("to", "be", "or", "not", "to", "be"))

""")

    run_shell(index, source.reader(index), tokenizer)


if __name__ == "__main__":
    main()
