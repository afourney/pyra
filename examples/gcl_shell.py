#!/usr/bin/python
import gzip
import re
import sys
import traceback
from pyra import InvertedIndex, GCL

def main():

    # Load the complete works of Shakespeare, and 
    # do some trivial tokenization. It works for this
    # corpus, but I would NOT advise its use for
    # other XML documents

    print("Loading Shakespeare XML corpus...")

    corpus = []
    f = gzip.open('shakespeare.xml.gz', 'r')
    for line in f:

        # Skip blank line
        if re.match(r'^\s*$', line):
            continue

        # Tokenize
        line = re.sub(r'<', ' <', line.lower().strip())
        line = re.sub(r'>', '> ', line)
        tokens = re.split(r'[^\w\/<>]+', line.strip())
        corpus.extend(tokens)
    f.close()

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

        # DOES NOT WORK YET
        # ("<title>".."</title>") < ("<play>".."</title>")         

        # TRY THIS HACK
        ("<play>", "<title>") .. "</title>"

    Return the titles of all plays containing the word 'henry'

        # DOES NOT WORK YET
        #(("<title>".."</title>") < ("<play>".."</title>")) > "henry"         

        (("<play>", "<title>") .. "</title>") > "henry"

    Return short play title (3 or few words)
    (Note: We have to include the tags in the token count)
        
        # DOES NOT WORK YET -- EVEN THIS HACK
        (("<play>", "<title>") .. "</title>") < [6] 

        # TRY THIS
        [6] > (("<play>", "<title>") .. "</title>")

Press Ctl-D to exit. 
""")


    while True:
        sys.stdout.write("\nGCL: ")

        l = sys.stdin.readline()
        if not l:
            break

        l = l.strip()

        if len(l) == 0:
            continue

        print("")
        try:
            query = gcl.parse(l)
            for r in query:
                res = "slice(%d,%d)\t%s" % (r.start, r.stop, " ".join(corpus[r])) 

                # Handle long lines
                if len(res) > 80:
                    res = res[0:76] + "..."
                print res

        except Exception:
            print(traceback.format_exc())


if __name__ == "__main__":
    main()
