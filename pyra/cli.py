"""Search a UTF-8 file interactively with GCL or ranked passage retrieval."""

from __future__ import annotations

import argparse
import os
import re
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


_HIGHLIGHT = "\x1b[30;43m"  # Black text on a yellow background.
_RESET = "\x1b[0m"


def _paint(text: str, marked: list[bool]) -> str:
    output: list[str] = []
    active = False
    for char, selected in zip(text, marked, strict=True):
        if selected != active:
            output.append(_HIGHLIGHT if selected else _RESET)
            active = selected
        output.append(char)
    if active:
        output.append(_RESET)
    return "".join(output)


def _shorten(text: str, highlight: slice | None = None) -> str:
    # Normalize whitespace while retaining the original match's character positions.
    clean = "".join(c if c.isprintable() else " " for c in text)
    chars: list[str] = []
    marked: list[bool] = []
    start, stop, _ = highlight.indices(len(text)) if highlight else (0, 0, 1)
    for word in re.finditer(r"\S+", clean):
        if chars:
            chars.append(" ")
            marked.append(marked[-1] and start <= word.start() < stop)
        chars.extend(word.group())
        marked.extend(start <= i < stop for i in range(word.start(), word.end()))
    text = "".join(chars)
    if len(text) > _PREVIEW_LENGTH:
        half = (_PREVIEW_LENGTH - 3) // 2
        head, tail = text[:half], text[-half:]
        if " " in head:
            head = head.rsplit(" ", 1)[0]
        if " " in tail:
            tail = tail.split(" ", 1)[1]
        marked = marked[: len(head)] + [False] * 3 + marked[-len(tail) :]
        text = f"{head} … {tail}"
    return _paint(text, marked) if highlight else text


def _preview(
    reader: PassageReader, region: slice, length: int, *, context: bool, highlight: bool = False
) -> str:
    match_start, match_stop, _ = region.indices(length)
    if match_start >= match_stop:
        return "(empty region)"
    start, stop = match_start, match_stop
    if context:
        start, stop = max(0, start - _CONTEXT_TOKENS), min(length, stop + _CONTEXT_TOKENS)
    # Fetch only the ends of large regions, not an entire chapter just to abbreviate it.
    edge = _PREVIEW_LENGTH // 2
    if stop - start > 2 * edge:
        text = reader[start : start + edge] + " … " + reader[stop - edge : stop]
    else:
        text = reader[start:stop]
    selected = None
    if context and highlight:
        # Measure through the boundary tokens to retain intervening punctuation exactly.
        left = len(reader[start : match_start + 1]) - len(reader[match_start : match_start + 1])
        right = len(reader[match_stop - 1 : stop]) - len(reader[match_stop - 1 : match_stop])
        selected = slice(left, len(text) - right)
    return _shorten(text, selected)


def _wrap_result(text: str, width: int) -> list[str]:
    # Wrap visible text, then apply color; escape codes must not affect page sizing.
    parts: list[str] = []
    marked: list[bool] = []
    active = False
    for part in re.split(r"(\x1b\[(?:30;43|0)m)", text):
        if part in (_HIGHLIGHT, _RESET):
            active = part == _HIGHLIGHT
        else:
            parts.append(part)
            marked.extend([active] * len(part))
    plain = "".join(parts)
    result: list[str] = []
    position = 0
    for number, line in enumerate(textwrap.wrap(plain, width=width, subsequent_indent="   ")):
        indent = "   " if number else ""
        content = line[len(indent) :]
        position = plain.index(content, position)
        result.append(indent + _paint(content, marked[position : position + len(content)]))
        position += len(content)
    return result


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
    color = (
        sys.stdout.isatty() and not os.environ.get("NO_COLOR") and os.environ.get("TERM") != "dumb"
    )
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

        preview = _preview(reader, region, length, context=ranked, highlight=color and ranked)
        label = f"{number}. [{region.start}:{region.stop}] "
        lines = _wrap_result(label + preview, width)
        if interactive and page_count and used_lines + len(lines) > budget:
            if not _more():
                return
            page_count = used_lines = 0
        print("\n".join(lines))
        count += 1
        page_count += 1
        used_lines += len(lines)
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
