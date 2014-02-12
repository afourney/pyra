from ply import *
import sys

tokens = (
    'INT',
    'STRING',
    'OP_AND',
    'OP_OR',
    'OP_BOUNDED_BY',
    'OP_CONTAINING',
    'OP_CONTAINED_IN',
    'COMMA',
    'LPAREN',
    'RPAREN',
    'LSPAREN',
    'RSPAREN'
)

# Simple tokens
t_OP_AND            = r'\^'
t_OP_OR             = r'\+'
t_OP_BOUNDED_BY     = r'\.\.\.?'
t_OP_CONTAINING     = r'>'
t_OP_CONTAINED_IN   = r'<'
t_COMMA             = r','
t_LPAREN            = r'\('
t_RPAREN            = r'\)'
t_LSPAREN           = r'\['
t_RSPAREN           = r'\]'

def t_INT(t):
    r'\d+'
    t.value = int(t.value)
    return t

def t_STRING(t):
    r'\"([^\\"]|(\\.))*\"'
    escaped = 0
    str = t.value[1:-1]
    new_str = ""
    for i in range(0, len(str)):
        c = str[i]
        if escaped:
            if c == "n":
                c = "\n"
            elif c == "t":
                c = "\t"
            new_str += c
            escaped = 0
        else:
            if c == "\\":
                escaped = 1
            else:
                new_str += c
    t.value = new_str
    return t


# These are the things that should be ignored.
t_ignore = ' \t'

# Handle errors.
def t_error(t):
    raise SyntaxError("syntax error on line %d near '%s'" % 
        (t.lineno, t.value))

# Build the lexer.
lex.lex()

# Hook for testing
def gcl_lex(expr):
    results = []

    lex.input(expr)
    for tok in iter(lex.token, None):
        results.append( (repr(tok.type), repr(tok.value)) )

    return results
