"""Shared types for token positions, inclusive extents, and parsed queries."""

from typing import TypeAlias

# Finite positions are integers; missing matches use positive or negative infinity.
Position: TypeAlias = int | float
Extent: TypeAlias = tuple[Position, Position]
ParseValue: TypeAlias = "str | int | tuple[ParseValue, ...]"
ParseTree: TypeAlias = tuple[ParseValue, ...]
