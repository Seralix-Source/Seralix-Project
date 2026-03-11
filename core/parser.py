from abc import ABC
from dataclasses import dataclass
from functools import partial, reduce
from typing import Text

from funcparserlib.lexer import Token
from funcparserlib.parser import *

from .keywords import kwlist
from .lexer import lexer

KEYWORD: dict[str, Parser[Token, Text]] = {
    keyword: tok('KEYWORD', keyword) for keyword in kwlist
}

SYMBOL: dict[str, Parser[Token, Text]] = {
    '(': tok('SYMBOL', '('),
    ')': tok('SYMBOL', ')'),
    '[': tok('SYMBOL', '['),
    ']': tok('SYMBOL', ']'),
    '{': tok('SYMBOL', '{'),
    '}': tok('SYMBOL', '}'),

    '.': tok('SYMBOL', '.'),
    ',': tok('SYMBOL', ','),
    ';': tok('SYMBOL', ';'),

    '**': tok('SYMBOL', '**'),
    '*': tok('SYMBOL', '*'),
    '/': tok('SYMBOL', '/'),
    '%': tok('SYMBOL', '%'),
    '+': tok('SYMBOL', '+'),
    '-': tok('SYMBOL', '-'),

    '<<': tok('SYMBOL', '<<'),
    '>>': tok('SYMBOL', '>>'),
    '&': tok('SYMBOL', '&'),
    '|': tok('SYMBOL', '|'),
    '~': tok('SYMBOL', '~'),
    '^': tok('SYMBOL', '^'),

    '->': tok('SYMBOL', '->'),

    '==': tok('SYMBOL', '=='),
    '!=': tok('SYMBOL', '!='),
    '<':  tok('SYMBOL', '<'),
    '<=': tok('SYMBOL', '<='),
    '>':  tok('SYMBOL', '>'),
    '>=': tok('SYMBOL', '>='),

    '?': tok('SYMBOL', '?'),
    ':': tok('SYMBOL', ':'),

    '=': tok('SYMBOL', '='),
}

@dataclass
class AST(ABC): ...
@dataclass
class Expr(AST, ABC): ...
@dataclass
class Stmt(AST, ABC): ...

expr = forward_decl()
gexpr = SYMBOL['('] + expr + SYMBOL[')'] >> (lambda match: match[1])

# -------------------------
# Terminals
# -------------------------

@dataclass
class Sequence(Expr):
    exprs: list[Expr]
sequence = (
    SYMBOL['[']
    + maybe(
        expr
        + many(SYMBOL[','] + expr >> (lambda m: m[1]))
        >> (lambda m: [m[0], *m[1]])
    )
    + SYMBOL[']']
    >> (lambda m: Sequence(m[1] or []))
)

@dataclass
class String(Expr):
    string: str
string = tok('STRING') >> (lambda s: String(s))

@dataclass
class Number(Expr):
    number: str
number = tok('NUMBER') >> (lambda n: Number(n))

@dataclass
class Name(Expr):
    name: str
name = tok('NAME') >> (lambda x: Name(x))

terminal = sequence | string | number | name
terminal |= gexpr

# -------------------------
# Sub-Terminals
# -------------------------

@dataclass
class Accessing(Expr):
    expr: Expr
    member: Name
accessing = SYMBOL['.'] + name >> (lambda m: partial(Accessing, member=m[1]))

@dataclass
class Indexing(Expr):
    expr: Expr
    indexes: list[Expr]
indexing = (
    SYMBOL['[']
    + (
        expr
        + many(SYMBOL[','] + expr >> (lambda m: m[1]))
        >> (lambda m: [m[0], *m[1]])
    )
    + SYMBOL[']']
    >> (lambda m: partial(Indexing, indexes=m[1]))
)

@dataclass
class Calling(Expr):
    expr: Expr
    arguments: list[Expr]
calling = (
    SYMBOL['(']
    + maybe(
        expr
        + many(SYMBOL[','] + expr >> (lambda m: m[1]))
        >> (lambda m: [m[0], *m[1]])
    )
    + SYMBOL[')']
    >> (lambda m: partial(Calling, arguments=m[1] or []))
)

subterminal = (
    terminal
    + many(accessing | indexing | calling)
    >> (lambda m: reduce(lambda e, f: f(e), m[1], m[0]))
)

# (Unary and Binary) Ops
@dataclass
class UnaryOp(Expr):
    op: str
    expr: Expr

@dataclass
class BinaryOp(Expr):
    op: str
    left: Expr
    right: Expr

pow = forward_decl()
pow.define(
    subterminal
    + maybe(SYMBOL['**'] + pow)
    >> (lambda m: BinaryOp(op=m[1][0], left=m[0], right=m[1][1]) if m[1] else m[0])
)

prefix = (
    maybe(SYMBOL['+'] | SYMBOL['-'] | SYMBOL['~']) + pow
    >> (lambda m: UnaryOp(op=m[0], expr=m[1]) if m[0] else m[1])
)

mul = (
    prefix
    + many((SYMBOL['*'] | SYMBOL['/'] | SYMBOL['%']) + prefix)
    >> (lambda m: reduce(lambda l, r: BinaryOp(op=r[0], left=l, right=r[1]), m[1], m[0]))
)

add = (
    mul
    + many((SYMBOL['+'] | SYMBOL['-']) + mul)
    >> (lambda m: reduce(lambda l, r: BinaryOp(op=r[0], left=l, right=r[1]), m[1], m[0]))
)

shift = (
    add
    + many((SYMBOL['<<'] | SYMBOL['>>']) + add)
    >> (lambda m: reduce(lambda l, r: BinaryOp(op=r[0], left=l, right=r[1]), m[1], m[0]))
)

bitand = (
    shift
    + many(SYMBOL['&'] + shift)
    >> (lambda m: reduce(lambda l, r: BinaryOp(op=r[0], left=l, right=r[1]), m[1], m[0]))
)

bitxor = (
    bitand
    + many(SYMBOL['^'] + bitand)
    >> (lambda m: reduce(lambda l, r: BinaryOp(op=r[0], left=l, right=r[1]), m[1], m[0]))
)

bitor = (
    bitxor
    + many(SYMBOL['|'] + bitxor)
    >> (lambda m: reduce(lambda l, r: BinaryOp(op=r[0], left=l, right=r[1]), m[1], m[0]))
)

cmp = (
    bitor
    + many((SYMBOL['=='] | SYMBOL['!='] | SYMBOL['<='] | SYMBOL['<'] | SYMBOL['>='] | SYMBOL['>']) + bitor)
    >> (lambda m: reduce(lambda l, r: BinaryOp(op=r[0], left=l, right=r[1]), m[1], m[0]))
)


@dataclass
class TernaryOp(Expr):
    condition: Expr
    iftrue: Expr
    iffalse: Expr

ternary = (
    cmp
    + maybe(
        SYMBOL['?']
        + expr
        + SYMBOL[':']
        + expr
    )
    >> (lambda m: TernaryOp(m[0], m[1][1], m[1][3]) if m[1] else m[0])
)

@dataclass
class ArrowFunction(Expr):
    @dataclass
    class Param(AST):
        name: Name
        default: Expr | None = None

    params: list[Param]
    returns: Expr

def arrow(m):
    defaulting = False
    for param in (params := m[1] or []):
        if param.default is not None:
            defaulting = True
        elif defaulting:
            raise SyntaxError

    return ArrowFunction(params=params, returns=m[4])

arrowparam = (
    name
    + maybe(SYMBOL['='] + expr >> (lambda m: m[1]))
    >> (lambda m: ArrowFunction.Param(m[0], m[1]))
)
arrowfunction = (
    SYMBOL['(']
    + maybe(
        arrowparam
        + many(SYMBOL[','] + arrowparam >> (lambda m: m[1]))
        >> (lambda m: [m[0], *m[1]])
    )
    + SYMBOL[')']
    + SYMBOL['->']
    + expr
    >>  arrow
)
arrowfunction |= ternary

expr.define(arrowfunction)


def parser(source: Text) -> AST:
    return expr.parse(lexer(source))
