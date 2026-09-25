"""Restartable text sources and checkpoint-assisted passage retrieval."""

from __future__ import annotations

import re
from collections.abc import Callable, Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import BinaryIO, Protocol


@dataclass(frozen=True)
class Token:
    """A normalized term and its exclusive-stop span in the tokenizer's input."""

    term: str
    start: int
    stop: int


class Tokenizer(Protocol):
    """Tokenize one line deterministically, returning ordered, nonoverlapping spans.

    Offsets count characters in the supplied line. Spans must be nonempty.
    Sources retain the original line context when resuming at a checkpoint.
    """

    def __call__(self, text: str) -> Iterator[Token]:
        """Yield normalized terms with their original character spans."""
        ...


class RegexTokenizer:
    """Find regex matches, normalize their terms, and optionally filter them.

    Defaults follow the Shakespeare demo: lowercase words and simple tags,
    retaining slashes and angle brackets. Boundaries occur before ``<``, after
    ``>``, and at characters outside Unicode word characters and ``/<>``.
    This is lightweight markup tokenization, not a general XML parser.
    """

    def __init__(
        self,
        pattern: str = r"<?[\w/]+>?|<>?|>",
        *,
        normalize: Callable[[str], str] = str.lower,
        keep: Callable[[str], bool] | None = None,
    ) -> None:
        """Configure token matching; filtering receives the normalized term."""
        self._pattern = re.compile(pattern)
        self._normalize = normalize
        self._keep = keep

    def __call__(self, text: str) -> Iterator[Token]:
        """Yield nonempty matches with unchanged source spans."""
        for match in self._pattern.finditer(text):
            if match.start() == match.end():
                raise ValueError("token patterns must not produce empty matches")
            term = self._normalize(match.group())
            if term and (self._keep is None or self._keep(term)):
                yield Token(term, match.start(), match.end())


class CheckpointIndex(Protocol):
    """The index information required by a passage reader."""

    @property
    def corpus_length(self) -> int:
        """Return the indexed token count."""
        ...

    def checkpoint(self, position: int) -> tuple[int, int]:
        """Return a token position and opaque source offset at or before position."""
        ...


class TextSource(Protocol):
    """Provide repeatable positioned tokens and access to their original text.

    Source contents and tokenization must stay unchanged for an index's lifetime.
    Source offsets are opaque to the index and interpreted only by the source.
    """

    def __iter__(self) -> Iterator[tuple[str, int]]:
        """Return a fresh iterator of (term, source offset) pairs."""
        ...

    def spans(self, offset: int = 0) -> Iterator[Token]:
        """Yield source-coordinate spans starting at or after a source offset."""
        ...

    def read(self, start: int, stop: int) -> str:
        """Read original text between source offsets, excluding stop."""
        ...

    def reader(self, index: CheckpointIndex) -> PassageReader:
        """Bind this source to an index built from its positioned tokens."""
        ...


class _TextSource:
    def __iter__(self) -> Iterator[tuple[str, int]]:
        for token in self.spans():
            yield token.term, token.start

    def spans(self, offset: int = 0) -> Iterator[Token]:
        raise NotImplementedError

    def read(self, start: int, stop: int) -> str:
        raise NotImplementedError

    def reader(self, index: CheckpointIndex) -> PassageReader:
        """Bind an index built from this source to a slice-based reader."""
        return PassageReader(self, index)


def _tokens(tokenizer: Tokenizer, line: str) -> Iterator[Token]:
    previous_stop = 0
    for token in tokenizer(line):
        if not 0 <= previous_stop <= token.start < token.stop <= len(line):
            raise ValueError("token spans must be ordered, nonoverlapping, and within the line")
        previous_stop = token.stop
        yield token


class StringTextSource(_TextSource):
    """Provide positioned tokens and passages from a string, using character offsets."""

    def __init__(self, text: str, *, tokenizer: Tokenizer | None = None) -> None:
        """Keep the original text and the deterministic, line-oriented tokenizer."""
        self._text = text
        self._tokenizer = tokenizer if tokenizer is not None else RegexTokenizer()

    def spans(self, offset: int = 0) -> Iterator[Token]:
        """Resume tokenization with the original containing-line context."""
        if not 0 <= offset <= len(self._text):
            raise ValueError("source offset outside the text")
        start = self._text.rfind("\n", 0, offset) + 1
        while start < len(self._text):
            newline = self._text.find("\n", start)
            stop = len(self._text) if newline < 0 else newline + 1
            for token in _tokens(self._tokenizer, self._text[start:stop]):
                if start + token.start >= offset:
                    yield Token(token.term, start + token.start, start + token.stop)
            start = stop

    def read(self, start: int, stop: int) -> str:
        """Return original text from start up to, but not including, stop."""
        return self._text[start:stop]


def _line_start(stream: BinaryIO, offset: int) -> int:
    cursor = offset
    while cursor:
        start = max(0, cursor - 4096)
        stream.seek(start)
        block = stream.read(cursor - start)
        newline = block.rfind(b"\n")
        if newline >= 0:
            return start + newline + 1
        cursor = start
    return 0


class FileTextSource(_TextSource):
    """Read a UTF-8 file line by line, using byte offsets and independent handles.

    Files must remain unchanged while their indexes are in use. No file handle
    is retained by the source or reader; each iteration or read opens its own.
    """

    def __init__(self, path: str | Path, *, tokenizer: Tokenizer | None = None) -> None:
        """Select a UTF-8 file and deterministic, line-oriented tokenizer."""
        self._path = Path(path).absolute()
        self._tokenizer = tokenizer if tokenizer is not None else RegexTokenizer()

    def spans(self, offset: int = 0) -> Iterator[Token]:
        """Resume at a byte offset, preserving the original line for tokenization."""
        with self._path.open("rb") as stream:
            stream.seek(0, 2)
            if not 0 <= offset <= stream.tell():
                raise ValueError("source offset outside the file")
            stream.seek(_line_start(stream, offset))
            while raw := stream.readline():
                base = stream.tell() - len(raw)
                line = raw.decode("utf-8")
                char_position = 0
                byte_position = base
                for token in _tokens(self._tokenizer, line):
                    byte_position += len(line[char_position : token.start].encode("utf-8"))
                    stop = byte_position + len(line[token.start : token.stop].encode("utf-8"))
                    if byte_position >= offset:
                        yield Token(token.term, byte_position, stop)
                    char_position = token.stop
                    byte_position = stop

    def read(self, start: int, stop: int) -> str:
        """Read a UTF-8 passage without newline translation."""
        if stop <= start:
            return ""
        with self._path.open("rb") as stream:
            stream.seek(start)
            return stream.read(stop - start).decode("utf-8")


class PassageReader:
    """Retrieve original text using exclusive-stop token slices and checkpoints.

    The index must have been built from this source's positioned tokens. Only
    unit-step slices are supported. Bounds follow Python slicing, including
    negative indices, omitted bounds, clipping, and empty slices.
    """

    def __init__(self, source: TextSource, index: CheckpointIndex) -> None:
        """Bind a source to its corresponding index without taking ownership."""
        self._source = source
        self._index = index

    def __getitem__(self, region: slice) -> str:
        """Return text from the first selected token's start to the last token's end."""
        if not isinstance(region, slice):  # pyright: ignore[reportUnnecessaryIsInstance]
            raise TypeError("passages require a token slice")
        start, stop, step = region.indices(self._index.corpus_length)
        if step != 1:
            raise ValueError("passage slices only support a step of 1")
        if start >= stop:
            return ""
        position, offset = self._index.checkpoint(start)
        first = None
        spans = self._source.spans(offset)
        try:
            for token in spans:
                if position == start:
                    first = token.start
                if position == stop - 1:
                    assert first is not None
                    return self._source.read(first, token.stop)
                position += 1
        finally:
            close = getattr(spans, "close", None)
            if close is not None:
                close()
        raise ValueError("source ended before the indexed passage; rebuild the index")
