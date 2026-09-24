"""Tokenize GCL expressions with PLY."""

from __future__ import annotations

from typing import NoReturn

from ply import lex

tokens = (
    "INT",
    "STRING",
    "OP_AND",
    "OP_OR",
    "OP_BOUNDED_BY",
    "OP_CONTAINING",
    "OP_CONTAINED_IN",
    "OP_NOT_CONTAINING",
    "OP_NOT_CONTAINED_IN",
    "OP_START_PROJECTION",
    "OP_END_PROJECTION",
    "COMMA",
    "LPAREN",  # Regular (round)
    "RPAREN",
    "LSPAREN",  # Square
    "RSPAREN",
    "LCPAREN",  # Curly
    "RCPAREN",  # Curly
    "PARAM",
)

# Simple tokens
t_OP_AND = r"\^"
t_OP_OR = r"\+"
t_OP_BOUNDED_BY = r"\.\.\.?"
t_OP_CONTAINING = r">"
t_OP_CONTAINED_IN = r"<"
t_OP_NOT_CONTAINING = r"/>"
t_OP_NOT_CONTAINED_IN = r"/<"
t_OP_START_PROJECTION = r"\_\{"
t_OP_END_PROJECTION = r"\}\_"
t_COMMA = r","
t_LPAREN = r"\("
t_RPAREN = r"\)"
t_LSPAREN = r"\["
t_RSPAREN = r"\]"
t_LCPAREN = r"\{"
t_RCPAREN = r"\}"


def t_INT(t: lex.LexToken) -> lex.LexToken:
    r"""\d+"""
    t.value = int(t.value)
    return t


def t_STRING(t: lex.LexToken) -> lex.LexToken:
    r"""\"([^\\"]|(\\.))*\""""
    escaped = 0
    str = t.value[1:-1]
    new_str = ""
    for i in range(0, len(str)):
        c = str[i]
        if escaped:
            new_str += c
            escaped = 0
        else:
            if c == "\\":
                escaped = 1
            else:
                new_str += c
    t.value = new_str
    return t


def t_PARAM(t: lex.LexToken) -> lex.LexToken:
    r"""%\d+"""
    t.value = t.value[1:]
    return t


# These are the things that should be ignored.
t_ignore = " \t"


# Handle errors.
def t_error(t: lex.LexToken) -> NoReturn:
    """Raise a syntax error for an unrecognized token."""
    raise SyntaxError(f"syntax error on line {t.lineno:d} near '{t.value}'")


# Build the lexer.
lex.lex()


# Hook for testing
def gcl_lex(expr: str) -> list[tuple[str, str]]:
    """Return token type and value representations for an expression."""
    results: list[tuple[str, str]] = []

    lex.input(expr)
    for tok in iter(lex.token, None):
        results.append((repr(tok.type), repr(tok.value)))

    return results
