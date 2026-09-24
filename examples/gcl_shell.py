#!/usr/bin/env python3
"""Run an interactive GCL shell over the bundled Shakespeare corpus."""

import gzip
import re
import sys
import traceback
from pathlib import Path

from pyra import GCL, InvertedIndex


def main():
    """Index Shakespeare and evaluate queries read from standard input."""
    # Uber-dangerous
    sys.setrecursionlimit(sys.getrecursionlimit() * 10)  # 10 times the space to play

    # Load the complete works of Shakespeare, and
    # do some trivial tokenization. It works for this
    # corpus, but I would NOT advise its use for
    # other XML documents

    print("Loading Shakespeare XML corpus...")

    corpus = []
    corpus_path = Path(__file__).with_name("shakespeare.xml.gz")
    with gzip.open(corpus_path, "rt", encoding="utf-8") as f:
        for line in f:
            # Skip blank line
            if re.match(r"^\s*$", line):
                continue

            # Tokenize
            line = re.sub(r"<", " <", line.lower().strip())
            line = re.sub(r">", "> ", line)
            tokens = re.split(r"[^\w\/<>]+", line.strip())
            corpus.extend(tokens)

    # Index the corpus
    print("Indexing corpus...")

    index = InvertedIndex(corpus)
    gcl = GCL(index)

    print("Done.")

    # The interactive shell

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


Press Ctl-D to exit.
""")

    while True:
        sys.stdout.write("\nGCL: ")

        line = sys.stdin.readline()
        if not line:
            break

        line = line.strip()

        if len(line) == 0:
            continue

        print("")
        try:
            query = gcl.parse(line)
            for r in query:
                res = f"slice({r.start:d},{r.stop:d}):\t{' '.join(corpus[r])}"

                # Handle long lines
                if len(res) > 80:
                    res = res[0:76] + "..."
                print(res)

        except Exception:  # noqa: BLE001 - Report query errors and keep the shell running.
            print(traceback.format_exc())


if __name__ == "__main__":
    main()
