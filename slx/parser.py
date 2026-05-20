import functools
from abc import ABC
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Text, Any, Literal
from unittest import skip

from funcparserlib.lexer import *
from funcparserlib.parser import *

from . import lexer


def op(lexeme: str) -> Parser[Token, Text]:
    return tok("OP", lexeme)


def wd(lexeme: str) -> Parser[Token, Text]:
    return tok("NAME", lexeme)


@dataclass
class AST(ABC): ...
@dataclass
class Expr(AST, ABC): ...
@dataclass
class Stmt(AST, ABC): ...


expr: Parser[Token, Expr | Any] = forward_decl()
stmt: Parser[Token, Stmt | Any] = forward_decl()


@dataclass
class GroupedExpr(Expr):
    expr: Expr
grouped_expr: Parser[Token, GroupedExpr] = op('(') + expr + op(')') >> (lambda match: GroupedExpr(expr=match[1]))


@dataclass
class Null(Expr):
    object: None
null_literal: Parser[Token, Null] = wd("null") >> (lambda match: Null(object=None))


@dataclass
class Bool(Expr):
    object: bool
bool_literal: Parser[Token, Bool] = (wd("true") | wd("false")) >> (lambda match: Bool(object=eval(match.capitalize())))


@dataclass
class Number(Expr):
    object: int | float | complex
number_literal: Parser[Token, Number] = tok("NUMBER") >> (lambda match: Number(object=eval(match)))


@dataclass
class String(Expr):
    object: str | bytes
string_literal: Parser[Token, String] = tok("STRING") >> (lambda match: String(object=eval(match)))


@dataclass
class List(Expr):
    object: list[Expr]
explicit_list: Parser[Token, List] = (
    skip(op('[')) +
    maybe((
        expr + many(skip(op(',')) + expr)
    ) >> (lambda match: [match[0], *match[1]])) +
    skip(op(']'))
) >> (lambda match: List(object=match or []))


@dataclass
class Dict(Expr):
    object: list[tuple[Expr, Expr]]
explicit_dict: Parser[Token, Dict] = (
    skip(op('{')) +
    maybe((
        ((expr + skip(op(':')) + expr) >> (lambda match: (match[0], match[1])))
        + many(skip(op(',')) + ((expr + skip(op(':')) + expr) >> (lambda match: (match[0], match[1]))))
    ) >> (lambda match: [match[0], *match[1]])) +
    skip(op('}'))
) >> (lambda match: Dict(object=match or []))


name: Parser[Token, Text] = tok("NAME")


atom: Parser[Token, Expr | Any] = null_literal | bool_literal | number_literal | string_literal | explicit_list | explicit_dict | name
atom |= grouped_expr

@dataclass
class Call(Expr):
    callee: Expr
    args: list[Expr]
    kwargs: dict[str, Expr]
def Calling(arguments: list[tuple[Expr, Expr | None]]) -> Callable[[Expr], Call]:  # NOQA: N802
    args, kwargs = [], {}

    for left, right in arguments:
        if right is None:
            if kwargs:
                raise SyntaxError("cannot mix positional and keyword arguments")
            args.append(left)
            continue
        if not isinstance(left, str):
            raise SyntaxError("cannot use a non-identifier as a keyword argument")
        kwargs[left] = right

    return lambda callee: Call(callee=callee, args=args, kwargs=kwargs)
_call_argument: Parser[Token, tuple[Expr, Expr | None]] = (expr + maybe(skip(op('=')) + expr)) >> (lambda match: (match[0], match[1]))
call: Parser[Token, Callable[[Expr], Call]] = (
    skip(op('(')) +
    maybe((
        _call_argument + many(skip(op(',')) + _call_argument)
    ) >> (lambda match: [match[0], *match[1]])) +
    skip(op(')'))
) >> (lambda match: Calling(match or []))


@dataclass
class MemberAccess(Expr):
    target: Expr
    member: str
member_access: Parser[Token, Callable[[Expr], MemberAccess]] = (
    skip(op('.')) + name
) >> (lambda member: lambda target: MemberAccess(target=target, member=member))


@dataclass
class SubscriptAccess(Expr):
    @dataclass
    class Slice(AST):
        start: Expr | None
        stop: Expr | None
        step: Expr | None

    target: Expr
    subscript: list[Expr | Slice]
_slice: Parser[Token, SubscriptAccess.Slice] = (
    maybe(expr) +
    skip(op(':')) +
    maybe(expr) +
    maybe(skip(op(':')) + maybe(expr))
) >> (lambda match: SubscriptAccess.Slice(start=match[0], stop=match[1], step=match[2]))
_index: Parser[Token, Expr] = (
    expr
)
_subscript: Parser[Token,  Expr | SubscriptAccess.Slice] = _slice | _index
subscript_access: Parser[Token, Callable[[Expr], SubscriptAccess]] = (
    skip(op('[')) +
    maybe((
        _subscript + many(skip(op(',')) + _subscript)
    ) >> (lambda match: [match[0], *match[1]])) +
    skip(op(']'))
) >> (lambda match: lambda target: SubscriptAccess(target=target, subscript=match or []))


postfix: Parser[Token, Callable[[Expr], Call | MemberAccess | SubscriptAccess]] = (
    atom + many(call | member_access | subscript_access)
) >> (lambda match: functools.reduce(lambda expr, partial: partial(expr), match[1], match[0]))


@dataclass
class UnaryOp(Expr):
    op: str
    operand: Expr

@dataclass
class BinaryOp(Expr):
    op: str
    operands: tuple[Expr, Expr]


(exponentiation := forward_decl()).define((
    postfix + many(skip(op('**')) + exponentiation)
) >> (lambda match: functools.reduce(
    lambda left, right: BinaryOp(op='**', operands=(left, right)),
    match[1],
    match[0]
)))

unary: Parser[Token, UnaryOp | Expr] = (
    many(op('~') | op('+') | op('-')) + exponentiation
) >> (lambda match: functools.reduce(
    lambda operand, operator: UnaryOp(op=operator, operand=operand),
    reversed(match[0]),
    match[1]
))

multiplicative: Parser[Token, BinaryOp | Expr] = (
    unary + many((op('*') | op('/') | op('//') | op('%')) + unary)
) >> (lambda match: functools.reduce(
    lambda left, right: BinaryOp(op=right[0], operands=(left, right[1])),
    match[1],
    match[0]
))

additive: Parser[Token, BinaryOp | Expr] = (
    multiplicative + many((op('+') | op('-')) + multiplicative)
) >> (lambda match: functools.reduce(
    lambda left, right: BinaryOp(op=right[0], operands=(left, right[1])),
    match[1],
    match[0]
))

bitwise_shift: Parser[Token, BinaryOp | Expr] = (
    additive + many((op('<<') | op('>>')) + additive)
) >> (lambda match: functools.reduce(
    lambda left, right: BinaryOp(op=right[0], operands=(left, right[1])),
    match[1],
    match[0]
))

bitwise_and: Parser[Token, BinaryOp | Expr] = (
    bitwise_shift + many(skip(op('&')) + bitwise_shift)
) >> (lambda match: functools.reduce(
    lambda left, right: BinaryOp(op='&', operands=(left, right)),
    match[1],
    match[0]
))

bitwise_xor: Parser[Token, BinaryOp | Expr] = (
    bitwise_and + many(skip(op('^')) + bitwise_and)
) >> (lambda match: functools.reduce(
    lambda left, right: BinaryOp(op='^', operands=(left, right)),
    match[1],
    match[0]
))

bitwise_or: Parser[Token, BinaryOp | Expr] = (
    bitwise_xor + many(skip(op('|')) + bitwise_xor)
) >> (lambda match: functools.reduce(
    lambda left, right: BinaryOp(op='|', operands=(left, right)),
    match[1],
    match[0]
))

comparison: Parser[Token, BinaryOp | Expr] = (
    bitwise_or + many((op('==') | op('!=') | op('<=') | op('>=') | op('<') | op('>')) + bitwise_or)
) >> (lambda match: functools.reduce(
    lambda left, right: BinaryOp(op=right[0], operands=(left, right[1])),
    match[1],
    match[0]
))

boolean_not: Parser[Token, UnaryOp | Expr] = (
    many(wd('not')) + comparison
) >> (lambda match: functools.reduce(
    lambda operand, _: UnaryOp(op='not', operand=operand),
    match[0],
    match[1]
))

boolean_and: Parser[Token, BinaryOp | Expr] = (
    boolean_not + many(skip(wd('and')) + boolean_not)
) >> (lambda match: functools.reduce(
    lambda left, right: BinaryOp(op='and', operands=(left, right)),
    match[1],
    match[0]
))

boolean_or: Parser[Token, BinaryOp | Expr] = (
    boolean_and + many(skip(wd('or')) + boolean_and)
) >> (lambda match: functools.reduce(
    lambda left, right: BinaryOp(op='or', operands=(left, right)),
    match[1],
    match[0]
))


@dataclass
class TernaryOp(Expr):
    condition: Expr
    if_true: Expr
    if_false: Expr
ternary_op: Parser[Token, TernaryOp | Expr] = (
    boolean_or + maybe(skip(op('?')) + expr + skip(op(':')) + expr)
) >> (lambda match: TernaryOp(condition=match[0], if_true=match[1][0], if_false=match[1][1]) if match[1] is not None else match[0])


@dataclass
class LambdaFunction(Expr):
    params: list[tuple[str, Expr | None]]
    returns: Expr
def LambdaFunctionParams(params: list[tuple[str, Expr | None]]) -> list[tuple[str, Expr | None]]:  # NOQA: N802
    defaulting = False
    for name, default in params:
        if defaulting and default is None:
            raise SyntaxError(f"non-default parameter {name!r} follows default parameter")
        defaulting = default is not None
    return params
_lambda_parameter: Parser[Token, tuple[str, Expr | None]] = (name + maybe(skip(op('=')) + expr)) >> (lambda match: (match[0], match[1]))
lambda_function: Parser[Token, LambdaFunction] = (
    skip(op('(')) +
    maybe((
        _lambda_parameter + many(skip(op(',')) + _lambda_parameter)
    ) >> (lambda match: LambdaFunctionParams([match[0], *match[1]]))) +
    skip(op(')')) +
    skip(op('->')) +
    expr
) >> (lambda match: LambdaFunction(params=match[0] or [], returns=match[1]))

expr.define(lambda_function | ternary_op)

codeblock: Parser[Token, list[Stmt]] = skip(op('{')) + many(stmt) + skip(op('}'))


@dataclass
class Return(Stmt):
    returns: Expr | None
returns: Parser[Token, Return] = (
    skip(wd('return')) + maybe(expr) + skip(op(';'))
) >> (lambda match: Return(returns=match))


@dataclass
class ForIn(Stmt):
    target: Expr
    iterable: Expr
    codeblock: list[Stmt]
forin_stmt: Parser[Token, ForIn] = (
    skip(wd('for')) + expr + skip(wd('in')) + expr + codeblock
) >> (lambda match: ForIn(target=match[0], iterable=match[1], codeblock=match[2]))


@dataclass
class While(Stmt):
    condition: Expr
    codeblock: list[Stmt]
while_stmt: Parser[Token, While] = (
    skip(wd('while')) + expr + codeblock
) >> (lambda match: While(condition=match[0], codeblock=match[1]))


@dataclass
class IfElse(Stmt):
    @dataclass
    class IfThen(AST):
        condition: Expr
        codeblock: list[Stmt]

    ifthens: list[IfThen]
    otherwise: list[Stmt]
ifelse_stmt: Parser[Token, IfElse] = (
    ((
        ((
            skip(wd('if')) + expr + codeblock
        ) >> (lambda match: IfElse.IfThen(condition=match[0], codeblock=match[1]))) +
        many((
             skip(wd('elif')) + expr + codeblock
        ) >> (lambda match: IfElse.IfThen(condition=match[0], codeblock=match[1])))
    ) >> (lambda match: [match[0], *match[1]])) +
    maybe(skip(wd('else')) + codeblock)
) >> (lambda match: IfElse(ifthens=match[0], otherwise=match[1] or []))

@dataclass
class Capsule(Stmt):
    name: str
    fields: list[tuple[str, Expr | None]]
    frozen: bool
def CapsuleFields(fields: list[tuple[str, Expr | None]]) -> list[tuple[str, Expr | None]]:  # NOQA: N802
    defaulting = False
    for name, default in fields:
        if defaulting and default is None:
            raise SyntaxError(f"non-default field {name!r} follows default field")
        defaulting = default is not None
    return fields
_capsule_field: Parser[Token, tuple[str, Expr | None]] = (name + maybe(skip(op('=')) + expr)) >> (lambda match: (match[0], match[1]))
capsule: Parser[Token, Capsule] = (
    (wd('struct') | wd('record')) + name + skip(op('(')) +
    maybe((
        _capsule_field + many(skip(op(',')) + _capsule_field)
    ) >> (lambda match: CapsuleFields([match[0], *match[1]]))) +
    skip(op(')'))
) >> (lambda match: Capsule(name=match[1], fields=match[2] or [], frozen=match[0] == 'record'))


@dataclass
class Function(Stmt):
    name: str
    params: list[tuple[str, Expr | None]]
    codeblock: list[Stmt]
def FunctionParams(params: list[tuple[str, Expr | None]]) -> list[tuple[str, Expr | None]]:  # NOQA: N802
    defaulting = False
    for name, default in params:
        if defaulting and default is None:
            raise SyntaxError(f"non-default parameter {name!r} follows default parameter")
        defaulting = default is not None
    return params
_function_param: Parser[Token, tuple[str, Expr | None]] = (name + maybe(skip(op('=')) + expr)) >> (lambda match: (match[0], match[1]))
function: Parser[Token, Function] = (
    skip(wd('function')) + name + skip(op('(')) + maybe((
        (_function_param + many(skip(op(',')) + _function_param)) >> (lambda match: FunctionParams([match[0], *match[1]]))
    )) + skip(op(')')) + codeblock
) >> (lambda match: Function(name=match[0], params=match[1] or [], codeblock=match[2]))


@dataclass
class Assign(Stmt):
    op: str
    target: Expr
    object: Expr
assign: Parser[Token, Assign] = (
    expr + (
        op('=')
        | op('+=')
        | op('-=')
        | op('*=')
        | op('/=')
        | op('//=')
        | op('%=')
        | op('**=')
        | op('&=')
        | op('|=')
        | op('^=')
        | op('<<=')
        | op('>>=')
    ) +
    expr +
    skip(op(';'))
) >> (lambda match: Assign(op=match[1], target=match[0], object=match[2]))


stmt.define(
    function
    | returns
    | forin_stmt
    | while_stmt
    | ifelse_stmt
    | assign
    | (capsule + skip(op(';')))
    | (expr + skip(op(';')))
)

def run(source: str) -> list[AST]:
    return many(stmt).parse(lexer.run(source))
