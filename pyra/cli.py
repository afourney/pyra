"""Search a UTF-8 file interactively with GCL or ranked passage retrieval."""

from __future__ import annotations

import argparse
import os
import shutil
import sys
import textwrap
from collections.abc import Iterable
from pathlib import Path
from typing import cast

from . import (
    GCL,
    CoverDensityRanking,
    FileTextSource,
    InvertedIndex,
    PassageReader,
    RegexTokenizer,
    Tokenizer,
)

_PAGE_SIZE = 10
_PREVIEW_LENGTH = 300
_CONTEXT_TOKENS = 8


def _shorten(text: str) -> str:
    # Remove terminal controls and collapse whitespace without changing punctuation.
    text = " ".join("".join(c if c.isprintable() else " " for c in text).split())
    if len(text) <= _PREVIEW_LENGTH:
        return text
    half = (_PREVIEW_LENGTH - 3) // 2
    head, tail = text[:half], text[-half:]
    # Prefer word boundaries, but still make progress on very long single tokens.
    if " " in head:
        head = head.rsplit(" ", 1)[0]
    if " " in tail:
        tail = tail.split(" ", 1)[1]
    return f"{head} … {tail}"


def _preview(reader: PassageReader, region: slice, length: int, *, context: bool) -> str:
    start, stop, _ = region.indices(length)
    if start >= stop:
        return "(empty region)"
    if context:
        start, stop = max(0, start - _CONTEXT_TOKENS), min(length, stop + _CONTEXT_TOKENS)
    # Fetch only the ends of large regions, not an entire chapter just to abbreviate it.
    edge = _PREVIEW_LENGTH // 2
    if stop - start > 2 * edge:
        text = reader[start : start + edge] + " … " + reader[stop - edge : stop]
    else:
        text = reader[start:stop]
    return _shorten(text)


def _read_key() -> str:
    if os.name == "nt":
        import msvcrt

        key = msvcrt.getwch()
        if key in ("\x00", "\xe0"):
            msvcrt.getwch()  # Consume the rest of a function or arrow key.
        if key == "\x03":
            raise KeyboardInterrupt
        return key

    import termios
    import tty

    fd = sys.stdin.fileno()
    settings = termios.tcgetattr(fd)
    try:
        # Keep keys entered immediately after the paging prompt appears.
        tty.setcbreak(fd, termios.TCSANOW)
        # Consume an escape sequence together so arrow keys don't leak into the prompt.
        return os.read(fd, 32).decode(errors="replace")
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, settings)


def _more() -> bool:
    print("Space: more · Any other key: back to query", end="", flush=True)
    try:
        return _read_key() == " "
    finally:
        print()


def _show_results(
    regions: Iterable[slice], reader: PassageReader, length: int, *, ranked: bool
) -> None:
    interactive = sys.stdin.isatty() and sys.stdout.isatty()
    width, height = shutil.get_terminal_size()
    width = max(20, width)
    budget = max(1, height - 4)
    count = page_count = used_lines = 0
    for number, region in enumerate(regions, 1):
        # One-result lookahead avoids prompting at the end of an exact ten-result page.
        if page_count == _PAGE_SIZE:
            if not interactive:
                print("More results available; paging requires an interactive terminal.")
                return
            if not _more():
                return
            page_count = used_lines = 0

        preview = _preview(reader, region, length, context=ranked)
        label = f"{number}. [{region.start}:{region.stop}] "
        lines = textwrap.wrap(label + preview, width=width, subsequent_indent="   ")
        if interactive and page_count and used_lines + len(lines) + 1 > budget:
            if not _more():
                return
            page_count = used_lines = 0
        print("\n".join(lines))
        print()
        count += 1
        page_count += 1
        used_lines += len(lines) + 1
    if not count:
        print("No results.")


def run_shell(index: InvertedIndex, reader: PassageReader, tokenizer: Tokenizer) -> None:
    """Run the shared query loop over a prepared index and its text reader."""
    gcl = GCL(index)
    ranking = CoverDensityRanking(index)
    print("Enter a GCL expression, or ? search terms for ranked passages.")
    print("Ctrl-C cancels; Ctrl-D (Windows: Ctrl-Z then Enter) exits.\n")
    while True:
        line = ""
        try:
            line = input("pyra> ").strip()
            if not line:
                continue
            ranked = line.startswith("? ") or line == "?"
            if ranked:
                terms = [token.term for token in tokenizer(line[1:])]
                if not terms:
                    print("Enter search terms after '? '.")
                    continue
                regions: Iterable[slice] = (region for region, _score in ranking.rank(terms))
            else:
                regions = gcl.parse(line)
            _show_results(regions, reader, index.corpus_length, ranked=ranked)
        except EOFError:
            print()
            return
        except KeyboardInterrupt:
            print("\nCancelled.")
        except SyntaxError as error:
            print(f"Query error: {error.msg}")
            source = error.text or line
            offset = error.offset or len(source) + 1
            print(f"  {source.expandtabs()}")
            print("  " + " " * len(source[: offset - 1].expandtabs()) + "^")
        except (ValueError, OSError, UnicodeError, RecursionError) as error:
            print(f"Query error: {error}")


def main(argv: list[str] | None = None) -> int:
    """Index one UTF-8 file and start a query prompt."""
    parser = argparse.ArgumentParser(
        description="Search a UTF-8 text file using GCL or ranked passages.",
        epilog=(
            'Use quoted, lowercase terms in GCL (e.g. "brown" ^ "fox"), or ? brown fox. '
            "Tokenization preserves simple XML tags and uses lowercase terms. "
            "The file must remain unchanged while the shell is running."
        ),
    )
    parser.add_argument("filename", type=Path, help="UTF-8 text file to index")
    args = parser.parse_args(argv)
    path = cast(Path, args.filename)
    if not path.is_file():
        parser.error(f"not a regular file: {path}")
    tokenizer = RegexTokenizer()
    source = FileTextSource(path, tokenizer=tokenizer)
    try:
        print(f"Indexing {path}...", flush=True)
        index = InvertedIndex(source)
        print(f"Pyra — {path.name} · {index.corpus_length:,} tokens\n")
        run_shell(index, source.reader(index), tokenizer)
    except (OSError, UnicodeError) as error:
        print(f"pyra: {error}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("\nCancelled.", file=sys.stderr)
        return 130
    return 0
