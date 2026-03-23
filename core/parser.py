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
    '+=': tok('SYMBOL', '+='),
    '-=': tok('SYMBOL', '-='),
    '*=': tok('SYMBOL', '*='),
    '/=': tok('SYMBOL', '/='),
    '%=': tok('SYMBOL', '%='),
    '**=': tok('SYMBOL', '**='),

    '&=': tok('SYMBOL', '&='),
    '|=': tok('SYMBOL', '|='),
    '^=': tok('SYMBOL', '^='),
    '<<=': tok('SYMBOL', '<<='),
    '>>=': tok('SYMBOL', '>>='),
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
    objects: list[Expr]
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
    object: str | bytes
string = tok('STRING') >> (lambda s: String(eval(s)))

@dataclass
class Number(Expr):
    object: int | float | complex
number = tok('NUMBER') >> (lambda n: Number(eval(n)))

@dataclass
class Name(Expr):
    id: str
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
    @dataclass
    class Slice(AST):
        start: Expr | None = None
        stop: Expr | None = None
        step: Expr | None = None

    expr: Expr
    subscript: Expr | Slice


slice = (
        maybe(expr)
        + SYMBOL[':']
        + maybe(expr)
        + maybe(SYMBOL[':'] + maybe(expr))
        >> (
            lambda m: Indexing.Slice(
                start=m[0],
                stop=m[2],
                step=m[3][1] if m[3] else None,
            )
        )
)
indexing = (
        SYMBOL['[']
        + (slice | expr)
        + SYMBOL[']']
        >> (lambda m: partial(Indexing, subscript=m[1]))
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

booland = (
    cmp
    + many(KEYWORD['and'] + cmp)
    >> (lambda m: reduce(lambda l, r: BinaryOp(op=r[0], left=l, right=r[1]), m[1], m[0]))
)

boolor = (
    booland
    + many(KEYWORD['or'] + booland)
    >> (lambda m: reduce(lambda l, r: BinaryOp(op=r[0], left=l, right=r[1]), m[1], m[0]))
)

@dataclass
class TernaryOp(Expr):
    condition: Expr
    iftrue: Expr
    iffalse: Expr

ternary = (
    boolor
    + maybe(SYMBOL['?'] + expr + SYMBOL[':'] + expr)
    >> (lambda m: TernaryOp(condition=m[0], iftrue=m[1][1], iffalse=m[1][3]) if m[1] else m[0])
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

stmt = forward_decl()

@dataclass
class Assignment(Stmt):
    op: str
    target: Expr
    object: Expr

assignment = (
    subterminal
    + (
        SYMBOL['='] |
        SYMBOL['+='] |
        SYMBOL['-='] |
        SYMBOL['*='] |
        SYMBOL['/='] |
        SYMBOL['%='] |
        SYMBOL['**='] |
        SYMBOL['&='] |
        SYMBOL['|='] |
        SYMBOL['^='] |
        SYMBOL['<<='] |
        SYMBOL['>>=']
    )
    + expr
    + SYMBOL[';']
    >> (lambda m: Assignment(op=m[1], target=m[0], object=m[2]))
)

@dataclass
class ExprStmt(Stmt):
    expr: Expr

exprstmt = (
    expr
    + SYMBOL[';']
    >> (lambda m: ExprStmt(expr=m[0]))
)

@dataclass
class IfElse(Stmt):
    @dataclass
    class Elif(AST):
        cond: Expr
        body: list[Stmt]

    cond: Expr
    body: list[Stmt]
    elifs: list[Elif]
    otherwise: list[Stmt] | None = None

block = (
    SYMBOL['{']
    + many(stmt)
    + SYMBOL['}']
    >> (lambda m: m[1])
)

elifpart = (
    KEYWORD['elif']
    + expr
    + block
    >> (lambda m: IfElse.Elif(cond=m[1], body=m[2]))
)

elsepart = (
    KEYWORD['else']
    + block
    >> (lambda m: m[1])
)

ifelse = (
    KEYWORD['if']
    + expr
    + block
    + many(elifpart)
    + maybe(elsepart)
    >> (lambda m: IfElse(
        cond=m[1],
        body=m[2],
        elifs=m[3],
        otherwise=m[4],
    ))
)

@dataclass
class While(Stmt):
    cond: Expr
    body: list[Stmt]

whileloop = (
    KEYWORD['while']
    + expr
    + block
    >> (lambda m: While(cond=m[1], body=m[2]))
)

@dataclass
class ForIn(Stmt):
    target: Name
    iterable: Expr
    body: list[Stmt]

forin = (
    KEYWORD['for']
    + name
    + KEYWORD['in']
    + expr
    + block
    >> (lambda m: ForIn(target=m[1], iterable=m[3], body=m[4]))
)

@dataclass
class Function(Stmt):
    @dataclass
    class Param(AST):
        name: Name
        default: Expr | None = None

    name: Name
    params: list[Param]
    body: list[Stmt]

def params(m):
    defaulting = False
    for param in (params := m or []):
        if param.default is not None:
            defaulting = True
        elif defaulting:
            raise SyntaxError("non-default parameter cannot follow default parameter")
    return params

param = (
    name
    + maybe(SYMBOL['='] + expr >> (lambda m: m[1]))
    >> (lambda m: Function.Param(m[0], m[1]))
)
function = (
    KEYWORD['function']
    + name
    + SYMBOL['(']
    + maybe(
        param
        + many(SYMBOL[','] + param >> (lambda m: m[1]))
        >> (lambda m: [m[0], *m[1]])
    )
    + SYMBOL[')']
    + block
    >> (lambda m: Function(
        name=m[1],
        params=params(m[3]),
        body=m[5],
    ))
)

@dataclass
class Return(Stmt):
    expr: Expr | None = None

returnstmt = (
        KEYWORD['return']
        + maybe(expr)
        + SYMBOL[';']
        >> (lambda m: Return(expr=m[1]))
)

stmt.define(forin | whileloop | ifelse | function | returnstmt | assignment | exprstmt)

def parser(source: Text) -> list[Stmt]:
    return many(stmt).parse(lexer(source))

__all__ = ['parser']
__all__ += (name for name, object in globals().items() if isinstance(object, type) and issubclass(object, AST))
