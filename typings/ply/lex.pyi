"""PLY lexer declarations; token values are transformed by user callbacks."""

from typing import Any

class LexToken:
    type: str
    value: Any
    lineno: int
    lexpos: int

def lex() -> object: ...
def input(s: str) -> None: ...
def token() -> LexToken | None: ...
