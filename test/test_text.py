import tempfile
import unittest
from pathlib import Path

from pyra import (
    GCL,
    CoverDensityRanking,
    FileTextSource,
    InvertedIndex,
    RegexTokenizer,
    StringTextSource,
    Token,
)


class TestTextSources(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.path = Path(self.directory.name) / "text.txt"

    def sources(self, text, tokenizer=None):
        self.path.write_bytes(text.encode("utf-8"))
        return (
            StringTextSource(text, tokenizer=tokenizer),
            FileTextSource(self.path, tokenizer=tokenizer),
        )

    def test_restartable_and_independent(self):
        for source in self.sources("Hello, WORLD! Again."):
            with self.subTest(source=type(source).__name__):
                expected = [("hello", 0), ("world", 7), ("again", 14)]
                self.assertEqual(list(source), expected)
                first, second = iter(source), iter(source)
                self.assertEqual(next(first), expected[0])
                self.assertEqual(next(first), expected[1])
                self.assertEqual(list(second), expected)
                self.assertEqual(list(first), expected[2:])
                self.assertEqual(list(source), expected)

    def test_unicode_offsets_and_original_text(self):
        text = "  Café, Straße!\r\n猫 🐈 jumps.  "
        string, file = self.sources(text)
        self.assertEqual(list(string), [("café", 2), ("strasse", 8), ("猫", 17), ("jumps", 21)])
        self.assertEqual(list(file), [("café", 2), ("strasse", 9), ("猫", 19), ("jumps", 28)])
        for source in (string, file):
            reader = source.reader(InvertedIndex(source))
            self.assertEqual(reader[:], "Café, Straße!\r\n猫 🐈 jumps")
            self.assertEqual(reader[1:3], "Straße!\r\n猫")
            self.assertEqual(reader[0:1], "Café")
            self.assertEqual(reader[-1:], "jumps")

    def test_slice_semantics(self):
        for source in self.sources("zero one two three"):
            reader = source.reader(InvertedIndex(source))
            self.assertEqual(reader[:2], "zero one")
            self.assertEqual(reader[2:], "two three")
            self.assertEqual(reader[-3:-1], "one two")
            self.assertEqual(reader[-99:99:1], "zero one two three")
            for region in (slice(2, 2), slice(3, 1), slice(99, None)):
                self.assertEqual(reader[region], "")
            for region in (slice(None, None, -1), slice(None, None, 2), slice(None, None, 0)):
                with self.assertRaises(ValueError):
                    reader[region]
            for region in (1, "text", (0, 1), slice(0.5, 2)):
                with self.assertRaises(TypeError):
                    reader[region]

    def test_empty_sources(self):
        for text in ("", " \r\n... 🐈"):
            for source in self.sources(text):
                self.assertEqual(list(source), [])
                reader = source.reader(InvertedIndex(source))
                self.assertEqual(reader[:], "")

    def test_query_and_ranking_results(self):
        for source in self.sources("A brown, FOX sleeps. Another brown fox runs."):
            index = InvertedIndex(source)
            reader = source.reader(index)
            self.assertEqual(
                [reader[region] for region in GCL(index).parse('"brown", "fox"')],
                ["brown, FOX", "brown fox"],
            )
            passages = [
                reader[region]
                for region, _score in CoverDensityRanking(index).rank(["brown", "fox"])
            ]
            self.assertCountEqual(
                passages,
                [
                    "brown",
                    "FOX",
                    "brown",
                    "fox",
                    "brown, FOX",
                    "FOX sleeps. Another brown",
                    "brown fox",
                ],
            )

    def test_filtering_and_normalization(self):
        tokenizer = RegexTokenizer(keep=lambda term: term != "the")
        for source in self.sources("The Brown -- the FOX!", tokenizer):
            self.assertEqual([term for term, _ in source], ["brown", "fox"])
            self.assertEqual(source.reader(InvertedIndex(source))[:], "Brown -- the FOX")
        self.assertEqual(list(RegexTokenizer(normalize=str.upper)("hello")), [Token("HELLO", 0, 5)])

    def test_checkpoint_resume_retains_line_context(self):
        # Lookbehind would fail if the tokenizer only saw the suffix starting
        # at the checkpoint token. Include multibyte text and long lines.
        text = "ignored\r\n" + "猫 " * 300 + "#Word " * 600 + "\r\n#Last"
        tokenizer = RegexTokenizer(r"(?<=#)\w+")
        for source in self.sources(text, tokenizer):
            index = InvertedIndex(source)
            reader = source.reader(index)
            self.assertEqual(index.corpus_length, 601)
            self.assertGreater(index.checkpoint(520)[0], 0)
            self.assertEqual(reader[520:522], "Word #Word")
            self.assertEqual(reader[599:], "Word \r\n#Last")
            self.assertEqual(reader[256:257], "Word")

    def test_file_reader_uses_checkpoint(self):
        _, source = self.sources("word\n" * 700)
        index = InvertedIndex(source)

        class RecordingSource(FileTextSource):
            def spans(self, offset=0):
                self.offset = offset
                return super().spans(offset)

        recording = RecordingSource(self.path)
        self.assertEqual(recording.reader(index)[600:602], "word\nword")
        self.assertEqual(recording.offset, index.checkpoint(600)[1])
        self.assertGreater(recording.offset, 0)

    def test_slices_against_original_spans(self):
        text = "  Héllo, WORLD!\r\nignored 猫 jumps...\n" * 100
        for source in self.sources(text, RegexTokenizer(keep=lambda term: term != "ignored")):
            spans = list(source.spans())
            reader = source.reader(InvertedIndex(source))
            for start in (0, 1, 254, 255, 256, 257, 398, 399):
                for length in (1, 2, 5, 99):
                    stop = min(len(spans), start + length)
                    self.assertEqual(
                        reader[start:stop], source.read(spans[start].start, spans[stop - 1].stop)
                    )

    def test_reader_accepts_checkpoint_protocol(self):
        source = StringTextSource("hello world")

        class Index:
            corpus_length = 2

            def checkpoint(self, position):
                return (0, 0)

        self.assertEqual(source.reader(Index())[1:], "world")

    def test_truncated_source(self):
        _, source = self.sources("one two three")
        reader = source.reader(InvertedIndex(source))
        self.path.write_text("one", encoding="utf-8")
        with self.assertRaises(ValueError):
            reader[:]

    def test_invalid_token_spans(self):
        def invalid(_line):
            yield Token("bad", 2, 1)

        for source in self.sources("text", invalid):
            with self.assertRaises(ValueError):
                list(source)
        with self.assertRaises(ValueError):
            list(RegexTokenizer(r"\w*")("text"))

    def test_invalid_utf8(self):
        self.path.write_bytes(b"hello \xff")
        with self.assertRaises(UnicodeDecodeError):
            list(FileTextSource(self.path))

    def test_passage_read_closes_file(self):
        _, source = self.sources("hello world\n" * 300)
        reader = source.reader(InvertedIndex(source))
        self.assertEqual(reader[0:1], "hello")
        # On Windows an outstanding file handle prevents this rename.
        self.path.rename(self.path.with_suffix(".moved"))
