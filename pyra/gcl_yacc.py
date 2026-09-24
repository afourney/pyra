"""Parse GCL expressions into operator trees with PLY."""

from __future__ import annotations

from typing import cast

from ply import yacc
from ply.lex import LexToken

from ._types import ParseTree

# PLY discovers this token declaration through module introspection.
from .gcl_lex import tokens as tokens

precedence = (
    (
        "left",
        "OP_BOUNDED_BY",
        "OP_CONTAINING",
        "OP_CONTAINED_IN",
        "OP_NOT_CONTAINING",
        "OP_NOT_CONTAINED_IN",
    ),
    ("left", "OP_AND", "OP_OR"),
    ("left", "OP_START_PROJECTION", "OP_END_PROJECTION"),
    ("left", "COMMA"),
)


def p_gcl_expr(t: yacc.YaccProduction) -> None:
    """gcl_expr : LPAREN gcl_expr RPAREN"""
    t[0] = t[2]


def p_gcl_start_projection(t: yacc.YaccProduction) -> None:
    """gcl_expr : OP_START_PROJECTION gcl_expr RCPAREN"""
    t[0] = ("Start", t[2])


def p_gcl_end_projection(t: yacc.YaccProduction) -> None:
    """gcl_expr : LCPAREN gcl_expr OP_END_PROJECTION"""
    t[0] = ("End", t[2])


def p_gcl_and(t: yacc.YaccProduction) -> None:
    """gcl_expr : gcl_expr OP_AND gcl_expr"""
    t[0] = ("And", t[1], t[3])


def p_gcl_or(t: yacc.YaccProduction) -> None:
    """gcl_expr : gcl_expr OP_OR gcl_expr"""
    t[0] = ("Or", t[1], t[3])


def p_gcl_bounded_by(t: yacc.YaccProduction) -> None:
    """gcl_expr : gcl_expr OP_BOUNDED_BY gcl_expr"""
    t[0] = ("BoundedBy", t[1], t[3])


def p_gcl_containing(t: yacc.YaccProduction) -> None:
    """gcl_expr : gcl_expr OP_CONTAINING gcl_expr"""
    t[0] = ("Containing", t[1], t[3])


def p_gcl_contained_in(t: yacc.YaccProduction) -> None:
    """gcl_expr : gcl_expr OP_CONTAINED_IN gcl_expr"""
    t[0] = ("ContainedIn", t[1], t[3])


def p_gcl_not_containing(t: yacc.YaccProduction) -> None:
    """gcl_expr : gcl_expr OP_NOT_CONTAINING gcl_expr"""
    t[0] = ("NotContaining", t[1], t[3])


def p_gcl_not_contained_in(t: yacc.YaccProduction) -> None:
    """gcl_expr : gcl_expr OP_NOT_CONTAINED_IN gcl_expr"""
    t[0] = ("NotContainedIn", t[1], t[3])


def p_gcl_length(t: yacc.YaccProduction) -> None:
    """gcl_expr : LSPAREN INT RSPAREN"""
    t[0] = ("Length", t[2])


def p_gcl_position(t: yacc.YaccProduction) -> None:
    """gcl_expr : INT"""
    t[0] = ("Position", t[1])


def p_gcl_param(t: yacc.YaccProduction) -> None:
    """gcl_expr : PARAM"""
    t[0] = ("Param", t[1])


def p_gcl_phrase(t: yacc.YaccProduction) -> None:
    """gcl_expr : phrase"""
    items = ["Phrase"]
    items.extend(t[1])
    t[0] = tuple(items)


def p_gcl_phrase_cont(t: yacc.YaccProduction) -> None:
    """phrase : STRING COMMA phrase"""
    items: list[str] = []
    items.append(t[1])
    items.extend(t[3])
    t[0] = items


def p_gcl_token(t: yacc.YaccProduction) -> None:
    """phrase : STRING"""
    t[0] = (t[1],)


def p_error(t: LexToken) -> None:
    """Report the token that caused a parse error."""
    print(f"Syntax error at '{t.value}'")


yacc.yacc(debug=0, write_tables=0)


def gcl_yacc_parse(expr: str) -> ParseTree:
    """Return the operator tree for a GCL expression."""
    return cast(ParseTree, yacc.parse(expr))
