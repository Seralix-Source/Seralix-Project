import math
import operator
from collections.abc import Callable, Generator
from contextlib import contextmanager
from dataclasses import dataclass
from functools import cache
from typing import Any

from rich import print as cprint
from rich.pretty import pprint

from core.parser import *

ops: dict[str, Callable[[Any, Any], Any] | Callable[[Any], Any]] = {
    'and': lambda x, y: x and y,
    'or': lambda x, y: x or y,
    '+': operator.add,
    '-': operator.sub,
    '*': operator.mul,
    '/': operator.truediv,
    '%': operator.mod,
    '**': operator.pow,
    '<<': operator.lshift,
    '>>': operator.rshift,
    '&': operator.and_,
    '|': operator.or_,
    '~': operator.inv,
    '^': operator.xor,
    '==': operator.eq,
    '!=': operator.ne,
    '<': operator.lt,
    '<=': operator.le,
    '>': operator.gt,
    '>=': operator.ge,
    '+=': operator.iadd,
    '-=': operator.isub,
    '*=': operator.imul,
    '/=': operator.itruediv,
    '%=': operator.imod,
    '**=': operator.ipow,
    '&=': operator.iand,
    '|=': operator.ior,
    '^=': operator.ixor,
    '<<=': operator.ilshift,
    '>>=': operator.irshift,
}


@dataclass
class _return_signal(Exception):  # NOQA: N801
    returns: object


class runner:  # NOQA: N801
    def __init__(self, source: str) -> None:
        self.null = type('nulltype', (), {
            '__new__': cache(lambda cls: super(type, cls).__new__(cls)),
            '__bool__': lambda self: False,
            '__module__': None,
        })()
        self._stack: list[dict] = [{
            'print': cprint,
            'pprint': pprint,
            'range': range,
            'bool': bool,
            'str': str,
            'int': int,
            'float': float,
            'complex': complex,
            'len': len,
            'null': self.null,
            'true': True,
            'false': False,
            'pi': math.pi,
            'round': round,
            'cis': lambda x: complex(math.cos(x), math.sin(x)),
        }]
        self.nodes: list[AST] = parser(source)

    @property
    def namespace(self) -> dict[str, Any]:
        return self._stack[-1]

    @contextmanager
    def calling(self) -> Generator[None]:
        self._stack.append(self.namespace.copy())
        try:
            yield
        finally:
            self._stack.pop()

    def mkcaller(self, node: ArrowFunction | Function) -> Callable[..., Any]:
        namespace: dict[str, Any] = self.namespace.copy() if len(self._stack) > 1 else {}  # keep alive for nested functions
        def caller(*varargs: Any) -> Any:
            with self.calling():
                self.namespace.update(namespace)
                if len(varargs) < sum(param.default is None for param in node.params):
                    raise TypeError(f'Expected {len(node.params)} arguments, got {len(varargs)}')
                for vararg, param in zip(varargs, node.params):
                    self.namespace[param.name.id] = vararg
                for param in node.params[len(varargs):]:
                    self.namespace[param.name.id] = self.exec(param.default)

                if isinstance(node, ArrowFunction):
                    return self.exec(node.returns)

                try:
                    for stmt in node.body:
                        self.exec(stmt)
                except _return_signal as signal:
                    return signal.returns

                return self.null

        caller.__name__ = '<lambda>' if not isinstance(node, Function) else node.name.id
        if isinstance(node, Function):
            self.namespace[caller.__name__] = caller
        return caller

    def exec(self, node: AST | None) -> Any:
        if not node:
            return None

        match node:
            case Function() | ArrowFunction():
                return self.mkcaller(node)

            case ExprStmt():
                self.exec(node.expr)

            case IfElse():
                if self.exec(node.cond):
                    for stmt in node.body:
                        self.exec(stmt)
                    return None
                for elseif in node.elifs:
                    if self.exec(elseif.cond):
                        for stmt in elseif.body:
                            self.exec(stmt)
                        return None
                for stmt in node.otherwise or ():
                    self.exec(stmt)

            case While():
                while self.exec(node.cond):
                    for stmt in node.body:
                        self.exec(stmt)

            case ForIn():
                for item in self.exec(node.iterable):
                    self.namespace[node.target.id] = item
                    for stmt in node.body:
                        self.exec(stmt)

            case Return():
                if len(self._stack) == 1:
                    raise TypeError('unexpected return statement in global scope')
                raise _return_signal(self.exec(node.expr) if node.expr else self.null)

            case Assignment():
                object: Any = self.exec(node.object)
                match node.target:
                    case Name():
                        if node.target.id in {'null', 'true', 'false'}:
                            raise TypeError(f'cannot assign to {node.target.id!r}')
                        if node.op == '=':
                            self.namespace[node.target.id] = object
                        else:
                            self.namespace[node.target.id] = ops[node.op](self.namespace[node.target.id], object)
                    case Accessing():
                        member: str = node.target.member.id
                        if node.op == '=':
                            setattr(self.exec(node.target.expr), member, object)
                        else:
                            setattr(self.exec(node.target.expr), member, ops[node.op](self.exec(node.target), object))
                    case Indexing():
                        match node.target.subscript:
                            case Indexing.Slice():
                                subscript = slice(self.exec(node.target.subscript.start),
                                                  self.exec(node.target.subscript.stop),
                                                  self.exec(node.target.subscript.step))
                            case _:
                                subscript = self.exec(node.target.subscript)
                        if node.op == '=':
                            operator.setitem(self.exec(node.target.expr), subscript, object)
                        else:
                            operator.setitem(self.exec(node.target.expr), subscript, ops[node.op](self.exec(node.target), object))
            case _:
                match node:
                    case Sequence():
                        return list(map(self.exec, node.objects))

                    case String() | Number():
                        return node.object

                    case Name():
                        return self.namespace[node.id]

                    case Accessing():
                        return getattr(self.exec(node.expr), node.member.id)

                    case Indexing():
                        match node.subscript:
                            case Indexing.Slice():
                                subscript = slice(self.exec(node.subscript.start),
                                                  self.exec(node.subscript.stop),
                                                  self.exec(node.subscript.step))
                            case _:
                                subscript = self.exec(node.subscript)
                        return operator.getitem(self.exec(node.expr), subscript)

                    case Calling():
                        return self.exec(node.expr)(*map(self.exec, node.arguments))

                    case UnaryOp():
                        match node.op:
                            case '+':
                                return self.exec(node.expr)
                            case '-':
                                return -self.exec(node.expr)
                            case _:
                                return ops[node.op](self.exec(node.expr))

                    case BinaryOp():
                        return ops[node.op](self.exec(node.left), self.exec(node.right))

                    case TernaryOp():
                        return self.exec(node.iftrue) if self.exec(node.condition) else self.exec(node.iffalse)

        return None


    def run(self) -> None:
        while self.nodes:
            self.exec(self.nodes.pop(0))

