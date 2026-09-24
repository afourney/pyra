#!/usr/bin/python
"""Construct and evaluate generalized concordance list expressions."""

from __future__ import annotations

from collections.abc import Callable, Hashable, Iterator

###### BEGIN -- CAREFULLY IMPORT PARSING SUPPORT #####
from importlib.util import find_spec
from typing import Self, cast

from ._types import Extent, ParseTree, ParseValue, Position
from .iindex import InvertedIndex

_parsing_support_loaded = find_spec("ply") is not None

if _parsing_support_loaded:
    from .gcl_yacc import gcl_yacc_parse
else:
    gcl_yacc_parse = None
###### END -- CAREFULLY IMPORT PARSING SUPPORT #####


INF = float("inf")


class GCL:
    """Build region algebra expressions over an inverted index."""

    def __init__(self, inverted_index: InvertedIndex) -> None:
        """Store the inverted index used to construct expressions."""
        self.__idx = inverted_index

    #
    # Elementary Generators
    #

    def Term(self, term: Hashable) -> PhraseGenerator:
        """Return regions matching a single term."""
        return self.Phrase(term)

    def Phrase(self, *tokens: Hashable) -> PhraseGenerator:
        """Return regions matching the given consecutive tokens."""
        return PhraseGenerator(self.__idx, *tokens)

    def Position(self, p: int) -> ListGenerator:
        """Return a region containing only position p."""
        return ListGenerator(self.__idx, (p, p))

    def Slice(self, s: slice) -> ListGenerator:
        """Return a region corresponding to a Python slice."""
        return ListGenerator(self.__idx, _slice2extent(s))

    def Length(self, length: int) -> FixedLengthGenerator:
        """Return all corpus windows of the given token length."""
        return FixedLengthGenerator(self.__idx, length)

    #
    # Binary Operators
    #
    def And(self, a: GCListGenerator, b: GCListGenerator) -> AndOperator:
        """Return minimal regions containing matches from both a and b."""
        return AndOperator(self.__idx, a, b)

    def Or(self, a: GCListGenerator, b: GCListGenerator) -> OrOperator:
        """Return minimal regions drawn from either a or b."""
        return OrOperator(self.__idx, a, b)

    def BoundedBy(self, a: GCListGenerator, b: GCListGenerator) -> BoundedByOperator:
        """Return minimal regions starting in a and ending in b."""
        return BoundedByOperator(self.__idx, a, b)

    def Containing(self, a: GCListGenerator, b: GCListGenerator) -> ContainingOperator:
        """Return regions in a that contain a region in b."""
        return ContainingOperator(self.__idx, a, b)

    def ContainedIn(self, a: GCListGenerator, b: GCListGenerator) -> ContainedInOperator:
        """Return regions in a contained in a region in b."""
        return ContainedInOperator(self.__idx, a, b)

    def NotContaining(self, a: GCListGenerator, b: GCListGenerator) -> NotContainingOperator:
        """Return regions in a that contain no region in b."""
        return NotContainingOperator(self.__idx, a, b)

    def NotContainedIn(self, a: GCListGenerator, b: GCListGenerator) -> NotContainedInOperator:
        """Return regions in a not contained in any region in b."""
        return NotContainedInOperator(self.__idx, a, b)

    #
    # Unary operators
    #
    def Start(self, a: GCListGenerator) -> StartOperator:
        """Return the starting position of each region in a."""
        return StartOperator(self.__idx, a)

    def End(self, a: GCListGenerator) -> EndOperator:
        """Return the ending position of each region in a."""
        return EndOperator(self.__idx, a)

    #
    # Support for parsing gcl queries
    #
    def parse(self, expr: str, *args: GCListGenerator) -> GCListGenerator:
        """Parse a GCL query, substituting args for one-based parameter references."""
        if gcl_yacc_parse is not None:
            tree = gcl_yacc_parse(expr)
            return self.__parse_helper(tree, args)
        else:
            raise NotImplementedError(
                "GCL parsing requires the 'ply' module. "
                "PLY can be installed with 'python -m pip install ply'. "
                "Alternatively, just manually create GCL expressions "
                "using the GCL factory methods. "
            )

    def __parse_helper(
        self, subtree: ParseTree, args: tuple[GCListGenerator, ...]
    ) -> GCListGenerator:
        op = cast(str, subtree[0])
        operands: list[ParseValue | GCListGenerator] = list(subtree[1:])

        if op not in ("Phrase", "Position", "Length", "Param"):
            for i in range(0, len(operands)):
                operands[i] = self.__parse_helper(cast(ParseTree, operands[i]), args)

        if op == "Param":
            p_idx = int(cast(str, operands[0])) - 1  # Parameter indices are 1-based
            if p_idx not in range(0, len(args)):
                raise ValueError(f"Unbound parameter '%{p_idx + 1:d}' in GCL expression.")
            else:
                return args[p_idx]
        else:
            # The parser emits factory names and operands matching the GCL grammar.
            factory = cast(Callable[..., GCListGenerator], getattr(self, op))
            return factory(*operands)


class GCListGenerator:
    """Provide directional iteration over a generalized concordance list."""

    def __init__(self, inverted_index: InvertedIndex) -> None:
        """Store the inverted index used by this generator."""
        self.__idx = inverted_index

    def __iter__(self) -> Iterator[slice]:
        """Iterate over matching regions as Python slices."""
        return self.iterator()

    @property
    def inverted_index(self) -> InvertedIndex:
        """Return the inverted index used by this generator."""
        return self.__idx

    def iterator(self, k: Position | None = None, **args: bool) -> Iterator[slice]:
        """Iterate from position k, optionally in reverse order."""
        reverse = False

        for arg, val in args.items():
            if arg == "reverse":
                reverse = val
            else:
                raise ValueError()

        if reverse:
            if k is None:
                k = self.__idx.corpus_length - 1
            return GCListGenerator._reverse_iterator(self, k)
        else:
            if k is None:
                k = 0
            return GCListGenerator._forward_iterator(self, k)

    def _first_starting_at_or_after(self, k: Position) -> Extent:
        raise NotImplementedError()

    def _first_ending_at_or_after(self, k: Position) -> Extent:
        raise NotImplementedError()

    def _last_ending_at_or_before(self, k: Position) -> Extent:
        raise NotImplementedError()

    def _last_starting_at_or_before(self, k: Position) -> Extent:
        raise NotImplementedError()

    class _forward_iterator:
        def __init__(self, generator: GCListGenerator, k: Position) -> None:
            self.__k = k
            self.__generator = generator

        def __iter__(self) -> Self:
            return self

        def __next__(self) -> slice:
            if self.__k == INF:
                raise StopIteration()

            u, v = self.__generator._first_starting_at_or_after(self.__k)

            if u != INF:
                self.__k = u + 1
                return _extent2slice((u, v))
            else:
                raise StopIteration()

    class _reverse_iterator:
        def __init__(self, generator: GCListGenerator, k: Position) -> None:
            self.__k = k
            self.__generator = generator

        def __iter__(self) -> Self:
            return self

        def __next__(self) -> slice:
            if self.__k < 0:
                raise StopIteration()

            u, v = self.__generator._last_ending_at_or_before(self.__k)

            if u >= 0:
                self.__k = v - 1
                return _extent2slice((u, v))
            else:
                raise StopIteration()


class ListGenerator(GCListGenerator):
    """Generate regions from an explicit list of inclusive extents."""

    def __init__(self, inverted_index: InvertedIndex, *extents: Extent) -> None:
        """Store the given inclusive extents in their supplied order."""
        super().__init__(inverted_index)
        self.__list = extents

    def _first_starting_at_or_after(self, k: Position) -> Extent:
        # First interval starting at or after k
        # TODO: Use binary search
        for i in range(0, len(self.__list)):
            if self.__list[i][0] >= k:
                return self.__list[i]
        return (INF, INF)

    def _first_ending_at_or_after(self, k: Position) -> Extent:
        # First interval starting at or after k
        # TODO: Use binary search
        for i in range(0, len(self.__list)):
            if self.__list[i][1] >= k:
                return self.__list[i]
        return (INF, INF)

    def _last_ending_at_or_before(self, k: Position) -> Extent:
        # Last interval ending at or before k
        # TODO: Use binary search
        for i in range(len(self.__list) - 1, -1, -1):
            if self.__list[i][1] <= k:
                return self.__list[i]
        return (-INF, -INF)

    def _last_starting_at_or_before(self, k: Position) -> Extent:
        # Last interval starting at or before k
        # TODO: Use binary search
        for i in range(len(self.__list) - 1, -1, -1):
            if self.__list[i][0] <= k:
                return self.__list[i]
        return (-INF, -INF)


class PhraseGenerator(GCListGenerator):
    """Generate regions matching a consecutive sequence of terms."""

    def __init__(self, inverted_index: InvertedIndex, *tokens: Hashable) -> None:
        """Store the sequence of tokens to match."""
        super().__init__(inverted_index)
        self.__phrase = tokens

    def _first_starting_at_or_after(self, k: Position) -> Extent:
        if k == 0:
            return self.__next_phrase(self.__phrase, -INF)
        else:
            return self.__next_phrase(self.__phrase, k - 1)

    def _first_ending_at_or_after(self, k: Position) -> Extent:
        return self.__next_phrase(self.__phrase, k - len(self.__phrase))

    def _last_ending_at_or_before(self, k: Position) -> Extent:
        return self.__prev_phrase(self.__phrase, k + 1)

    def _last_starting_at_or_before(self, k: Position) -> Extent:
        return self.__prev_phrase(self.__phrase, k + len(self.__phrase))

    # Helper methods for phrases
    def __next_phrase(self, tokens: tuple[Hashable, ...], position: Position) -> Extent:
        v = position
        for i in range(0, len(tokens)):
            v = self.inverted_index.next(tokens[i], v)
        if v == INF:
            return (INF, INF)
        u = v
        for i in range(len(tokens) - 2, -1, -1):
            u = self.inverted_index.prev(tokens[i], u)
        if v - u == len(tokens) - 1:
            return (u, v)
        else:
            return self.__next_phrase(tokens, u)

    def __prev_phrase(self, tokens: tuple[Hashable, ...], position: Position) -> Extent:
        v = position
        for i in range(len(tokens) - 1, -1, -1):
            v = self.inverted_index.prev(tokens[i], v)
        if v == -INF:
            return (-INF, -INF)
        u = v
        for i in range(1, len(tokens)):
            u = self.inverted_index.next(tokens[i], u)
        if u - v == len(tokens) - 1:
            return (v, u)
        else:
            return self.__prev_phrase(tokens, u)


class FixedLengthGenerator(GCListGenerator):
    """Generate fixed-length windows over the indexed corpus."""

    def __init__(self, inverted_index: InvertedIndex, length: int) -> None:
        """Store the index and desired window length."""
        super().__init__(inverted_index)
        self.__length = length

    def _first_starting_at_or_after(self, k: Position) -> Extent:

        if k >= self.inverted_index.corpus_length:
            return (INF, INF)

        if k < 0:
            k = 0

        v = k + self.__length - 1

        # Overflow, no way to fix
        if v >= self.inverted_index.corpus_length:
            return (INF, INF)
        else:
            return (k, v)

    def _first_ending_at_or_after(self, k: Position) -> Extent:

        if k >= self.inverted_index.corpus_length:
            return (INF, INF)

        if k < 0:
            k = 0

        u = k - self.__length + 1

        # Underflow, try to fix
        if u < 0:
            d = 0 - u
            k += d
            u += d

            if k >= self.inverted_index.corpus_length:
                return (INF, INF)
            else:
                return (u, k)
        else:
            return (u, k)

    def _last_ending_at_or_before(self, k: Position) -> Extent:
        if k < 0:
            return (-INF, -INF)

        if k >= self.inverted_index.corpus_length:
            k = self.inverted_index.corpus_length - 1

        u = k - self.__length + 1

        # Underflow, no way to fix
        if u < 0:
            return (-INF, -INF)
        else:
            return (u, k)

    def _last_starting_at_or_before(self, k: Position) -> Extent:
        if k < 0:
            return (-INF, -INF)

        if k >= self.inverted_index.corpus_length:
            k = self.inverted_index.corpus_length - 1

        v = k + self.__length - 1

        # Overflowed, try to fix!
        if v >= self.inverted_index.corpus_length:
            d = v - self.inverted_index.corpus_length + 1
            k -= d
            v -= d

            if k < 0:
                return (-INF, -INF)
            else:
                return (k, v)
        else:
            return (k, v)


class AndOperator(GCListGenerator):
    """Generate minimal regions containing matches from both operands."""

    def __init__(
        self, inverted_index: InvertedIndex, a: GCListGenerator, b: GCListGenerator
    ) -> None:
        """Store the index and operand generators."""
        super().__init__(inverted_index)
        self.__a = a
        self.__b = b

    def _first_starting_at_or_after(self, k: Position) -> Extent:
        a = self.__a
        b = self.__b

        ua, va = a._first_starting_at_or_after(k)
        if ua == INF or va == INF:
            return (INF, INF)

        ub, vb = b._first_starting_at_or_after(k)
        if ub == INF or vb == INF:
            return (INF, INF)

        u0, v0 = a._last_ending_at_or_before(max(va, vb))
        if u0 == -INF or v0 == -INF:
            return (INF, INF)

        u1, v1 = b._last_ending_at_or_before(max(va, vb))
        if u1 == -INF or v1 == -INF:
            return (INF, INF)

        return (min(u0, u1), max(v0, v1))

    def _first_ending_at_or_after(self, k: Position) -> Extent:

        u, _v = self._last_ending_at_or_before(k - 1)
        return self._first_starting_at_or_after(u + 1)

    def _last_ending_at_or_before(self, k: Position) -> Extent:
        a = self.__a
        b = self.__b

        ua, va = a._last_ending_at_or_before(k)
        if ua == -INF or va == -INF:
            return (-INF, -INF)

        ub, vb = b._last_ending_at_or_before(k)
        if ub == -INF or vb == -INF:
            return (-INF, -INF)

        u0, v0 = a._first_starting_at_or_after(min(ua, ub))
        if u0 == INF or v0 == INF:
            return (-INF, -INF)

        u1, v1 = b._first_starting_at_or_after(min(ua, ub))
        if u1 == INF or v1 == INF:
            return (-INF, -INF)

        return (min(u0, u1), max(v0, v1))

    def _last_starting_at_or_before(self, k: Position) -> Extent:

        _u, v = self._first_starting_at_or_after(k + 1)
        return self._last_ending_at_or_before(v - 1)


class OrOperator(GCListGenerator):
    """Generate minimal regions drawn from either operand."""

    def __init__(
        self, inverted_index: InvertedIndex, a: GCListGenerator, b: GCListGenerator
    ) -> None:
        """Store the index and operand generators."""
        super().__init__(inverted_index)
        self.__a = a
        self.__b = b

    def _first_starting_at_or_after(self, k: Position) -> Extent:
        a = self.__a
        b = self.__b

        # Implementation from journal paper
        ua, va = a._first_starting_at_or_after(k)
        ub, vb = b._first_starting_at_or_after(k)

        if va < vb:
            return (ua, va)
        elif va > vb:
            return (ub, vb)
        else:
            return (max(ua, ub), va)

    def _first_ending_at_or_after(self, k: Position) -> Extent:

        # Implementation from journal paper
        u, _v = self._last_ending_at_or_before(k - 1)
        return self._first_starting_at_or_after(u + 1)

    def _last_ending_at_or_before(self, k: Position) -> Extent:
        a = self.__a
        b = self.__b

        # My implementation
        ua, va = a._last_ending_at_or_before(k)
        ub, vb = b._last_ending_at_or_before(k)

        if ua > ub:
            return (ua, va)
        elif ua < ub:
            return (ub, vb)
        else:
            return (ua, min(va, vb))

    def _last_starting_at_or_before(self, k: Position) -> Extent:

        _u, v = self._first_starting_at_or_after(k + 1)
        return self._last_ending_at_or_before(v - 1)


class BoundedByOperator(GCListGenerator):
    """Generate minimal regions starting in one operand and ending in another."""

    def __init__(
        self, inverted_index: InvertedIndex, a: GCListGenerator, b: GCListGenerator
    ) -> None:
        """Store the index and operand generators."""
        super().__init__(inverted_index)
        self.__a = a
        self.__b = b

    def _first_starting_at_or_after(self, k: Position) -> Extent:
        a = self.__a
        b = self.__b

        u0, v0 = a._first_starting_at_or_after(k)
        if u0 == INF or v0 == INF:
            return (INF, INF)

        u1, v1 = b._first_starting_at_or_after(v0 + 1)
        if u1 == INF or v1 == INF:
            return (INF, INF)

        u2, _v2 = a._last_ending_at_or_before(u1 - 1)
        return (u2, v1)

    def _first_ending_at_or_after(self, k: Position) -> Extent:

        u, _v = self._last_ending_at_or_before(k - 1)
        return self._first_starting_at_or_after(u + 1)

    def _last_ending_at_or_before(self, k: Position) -> Extent:
        a = self.__a
        b = self.__b

        u0, v0 = b._last_ending_at_or_before(k)
        if u0 == -INF or v0 == -INF:
            return (-INF, -INF)

        u1, v1 = a._last_ending_at_or_before(u0 - 1)
        if u1 == -INF or v1 == -INF:
            return (-INF, -INF)

        _u2, v2 = b._first_starting_at_or_after(v1 + 1)
        return (u1, v2)

    def _last_starting_at_or_before(self, k: Position) -> Extent:

        _u, v = self._first_starting_at_or_after(k + 1)
        return self._last_ending_at_or_before(v - 1)


class ContainingOperator(GCListGenerator):
    """Select regions from the first operand that contain a second-operand region."""

    def __init__(
        self, inverted_index: InvertedIndex, a: GCListGenerator, b: GCListGenerator
    ) -> None:
        """Store the index and operand generators."""
        super().__init__(inverted_index)
        self.__a = a
        self.__b = b

    def _first_starting_at_or_after(self, k: Position) -> Extent:
        a = self.__a

        u, v = a._first_starting_at_or_after(k)
        if u == INF or v == INF:
            return (INF, INF)

        return self._first_ending_at_or_after(v)

    def _first_ending_at_or_after(self, k: Position) -> Extent:
        a = self.__a
        b = self.__b

        while k < INF:
            # Get the first candidate match for A
            u0, v0 = a._first_ending_at_or_after(k)
            if u0 == INF or v0 == INF:
                return (INF, INF)

            # Get the first candidate match for B
            u1, v1 = b._first_starting_at_or_after(u0)
            if u1 == INF or v1 == INF:
                return (INF, INF)

            # We know u1 >= u0
            # Check containment by verifying that v1 <= v0
            if v1 <= v0:
                return (u0, v0)
            else:
                # Keep looking
                k = v1

        return (INF, INF)

    def _last_ending_at_or_before(self, k: Position) -> Extent:
        a = self.__a

        u, v = a._last_ending_at_or_before(k)
        if u == -INF or v == -INF:
            return (-INF, -INF)

        return self._last_starting_at_or_before(u)

    def _last_starting_at_or_before(self, k: Position) -> Extent:
        a = self.__a
        b = self.__b

        while k > -INF:
            u0, v0 = a._last_starting_at_or_before(k)
            if u0 == -INF or v0 == -INF:
                return (-INF, -INF)

            u1, v1 = b._last_ending_at_or_before(v0)
            if u1 == -INF or v1 == -INF:
                return (-INF, -INF)

            if u1 >= u0:
                return (u0, v0)
            else:
                # Keep looking
                k = u1

        return (-INF, -INF)


class ContainedInOperator(GCListGenerator):
    """Select regions from the first operand contained in a second-operand region."""

    def __init__(
        self, inverted_index: InvertedIndex, a: GCListGenerator, b: GCListGenerator
    ) -> None:
        """Store the index and operand generators."""
        super().__init__(inverted_index)
        self.__a = a
        self.__b = b

    def _first_starting_at_or_after(self, k: Position) -> Extent:
        a = self.__a
        b = self.__b

        while k < INF:
            u0, v0 = a._first_starting_at_or_after(k)

            if u0 == INF or v0 == INF:
                return (INF, INF)

            u1, v1 = b._first_ending_at_or_after(v0)

            if u1 == INF or v1 == INF:
                return (INF, INF)

            if u1 <= u0:
                return (u0, v0)
            else:
                # Keep looking
                k = u1

        return (INF, INF)

    def _first_ending_at_or_after(self, k: Position) -> Extent:
        a = self.__a

        u, v = a._first_ending_at_or_after(k)
        if u == INF or v == INF:
            return (INF, INF)

        return self._first_starting_at_or_after(u)

    def _last_ending_at_or_before(self, k: Position) -> Extent:
        a = self.__a
        b = self.__b

        while k > -INF:
            u0, v0 = a._last_ending_at_or_before(k)
            if u0 == -INF or v0 == -INF:
                return (-INF, -INF)

            u1, v1 = b._last_starting_at_or_before(u0)
            if u1 == -INF or v1 == -INF:
                return (-INF, -INF)

            if v1 >= v0:
                return (u0, v0)
            else:
                # Keep looking
                k = v1

        return (-INF, -INF)

    def _last_starting_at_or_before(self, k: Position) -> Extent:
        a = self.__a

        u, v = a._last_starting_at_or_before(k)
        if u == -INF or v == -INF:
            return (-INF, -INF)

        return self._last_ending_at_or_before(v)


class NotContainingOperator(GCListGenerator):
    """Select first-operand regions that contain no second-operand region."""

    def __init__(
        self, inverted_index: InvertedIndex, a: GCListGenerator, b: GCListGenerator
    ) -> None:
        """Store the index and operand generators."""
        super().__init__(inverted_index)
        self.__a = a
        self.__b = b

    def _first_starting_at_or_after(self, k: Position) -> Extent:
        a = self.__a

        u, v = a._first_starting_at_or_after(k)
        if u == INF or v == INF:
            return (INF, INF)

        return self._first_ending_at_or_after(v)

    def _first_ending_at_or_after(self, k: Position) -> Extent:
        a = self.__a
        b = self.__b

        u0, v0 = a._first_ending_at_or_after(k)
        while u0 < INF and v0 < INF:
            u1, v1 = b._first_starting_at_or_after(u0)

            if v1 > v0:
                return (u0, v0)
            else:
                # Skip extents that also contain this occurrence of B.
                u0, v0 = a._first_starting_at_or_after(u1 + 1)

        return (INF, INF)

    def _last_ending_at_or_before(self, k: Position) -> Extent:
        a = self.__a

        u, v = a._last_ending_at_or_before(k)
        if u == -INF or v == -INF:
            return (-INF, -INF)

        return self._last_starting_at_or_before(u)

    def _last_starting_at_or_before(self, k: Position) -> Extent:
        a = self.__a
        b = self.__b

        u0, v0 = a._last_starting_at_or_before(k)
        while u0 > -INF and v0 > -INF:
            u1, v1 = b._last_ending_at_or_before(v0)

            if u1 < u0:
                return (u0, v0)
            else:
                # Skip extents that also contain this occurrence of B.
                u0, v0 = a._last_ending_at_or_before(v1 - 1)

        return (-INF, -INF)


class NotContainedInOperator(GCListGenerator):
    """Select first-operand regions not contained in any second-operand region."""

    def __init__(
        self, inverted_index: InvertedIndex, a: GCListGenerator, b: GCListGenerator
    ) -> None:
        """Store the index and operand generators."""
        super().__init__(inverted_index)
        self.__a = a
        self.__b = b

    def _first_starting_at_or_after(self, k: Position) -> Extent:
        a = self.__a
        b = self.__b

        u0, v0 = a._first_starting_at_or_after(k)
        while u0 < INF and v0 < INF:
            u1, v1 = b._first_ending_at_or_after(v0)

            if u1 > u0:
                return (u0, v0)
            else:
                # Skip extents that are also contained in this occurrence of B.
                u0, v0 = a._first_ending_at_or_after(v1 + 1)

        return (INF, INF)

    def _first_ending_at_or_after(self, k: Position) -> Extent:
        a = self.__a

        u, v = a._first_ending_at_or_after(k)
        if u == INF or v == INF:
            return (INF, INF)

        return self._first_starting_at_or_after(u)

    def _last_ending_at_or_before(self, k: Position) -> Extent:
        a = self.__a
        b = self.__b

        u0, v0 = a._last_ending_at_or_before(k)
        while u0 > -INF and v0 > -INF:
            u1, v1 = b._last_starting_at_or_before(u0)

            if v1 < v0:
                return (u0, v0)
            else:
                # Skip extents that are also contained in this occurrence of B.
                u0, v0 = a._last_starting_at_or_before(u1 - 1)

        return (-INF, -INF)

    def _last_starting_at_or_before(self, k: Position) -> Extent:
        a = self.__a

        u, v = a._last_starting_at_or_before(k)
        if u == -INF or v == -INF:
            return (-INF, -INF)

        return self._last_ending_at_or_before(v)


class StartOperator(GCListGenerator):
    """Project each region onto its starting position."""

    def __init__(self, inverted_index: InvertedIndex, a: GCListGenerator) -> None:
        """Store the index and operand generators."""
        super().__init__(inverted_index)
        self.__a = a

    def _first_starting_at_or_after(self, k: Position) -> Extent:
        u, _v = self.__a._first_starting_at_or_after(k)
        return (u, u)

    def _first_ending_at_or_after(self, k: Position) -> Extent:
        u, _v = self.__a._first_starting_at_or_after(k)
        return (u, u)

    def _last_ending_at_or_before(self, k: Position) -> Extent:
        u, _v = self.__a._last_starting_at_or_before(k)
        return (u, u)

    def _last_starting_at_or_before(self, k: Position) -> Extent:
        u, _v = self.__a._last_starting_at_or_before(k)
        return (u, u)


class EndOperator(GCListGenerator):
    """Project each region onto its ending position."""

    def __init__(self, inverted_index: InvertedIndex, a: GCListGenerator) -> None:
        """Store the index and operand generators."""
        super().__init__(inverted_index)
        self.__a = a

    def _first_starting_at_or_after(self, k: Position) -> Extent:
        _u, v = self.__a._first_ending_at_or_after(k)
        return (v, v)

    def _first_ending_at_or_after(self, k: Position) -> Extent:
        _u, v = self.__a._first_ending_at_or_after(k)
        return (v, v)

    def _last_ending_at_or_before(self, k: Position) -> Extent:
        _u, v = self.__a._last_ending_at_or_before(k)
        return (v, v)

    def _last_starting_at_or_before(self, k: Position) -> Extent:
        _u, v = self.__a._last_ending_at_or_before(k)
        return (v, v)


#
# Helper method for converting extents to python slices
#


def _extent2slice(extent: Extent) -> slice:
    start = extent[0]
    stop = extent[1]

    if start == -INF:
        start = None

    if stop == INF:
        stop = None
    else:
        stop += 1

    return slice(start, stop)


def _slice2extent(s: slice) -> Extent:
    start = s.start
    stop = s.stop

    if start is None:
        start = -INF

    if stop is None:
        stop = INF
    elif stop == 0:
        stop = -INF

    return (start, stop - 1)
