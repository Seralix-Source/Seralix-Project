from collections import deque
from collections.abc import Callable
from dataclasses import dataclass
from typing import TypedDict, ClassVar, NoReturn, Literal, Any

from rich import print
from rich.pretty import pprint

from slx import parser
from slx.parser import *


@dataclass
class AuxExpr(Expr):
    object: Any


class Operator(TypedDict):
    callee: tuple[Callable[..., Any]] | tuple[Callable[..., Any], Callable[..., Any]]
    arity: Literal['unary', 'binary', 'multi', 'assign']
    inplace: bool

operators: dict[str, Operator] = {
    # Arithmetic
    '+':   {'callee': (lambda x: +x, lambda x, y: x + y),   'arity': 'multi', 'inplace': False},
    '-':   {'callee': (lambda x: -x, lambda x, y: x - y),   'arity': 'multi', 'inplace': False},
    '*':   {'callee': (lambda x, y: x * y,),   'arity': 'binary', 'inplace': False},
    '/':   {'callee': (lambda x, y: x / y,),   'arity': 'binary', 'inplace': False},
    '//':  {'callee': (lambda x, y: x // y,),  'arity': 'binary', 'inplace': False},
    '%':   {'callee': (lambda x, y: x % y,),   'arity': 'binary', 'inplace': False},
    '**':  {'callee': (lambda x, y: x ** y,),  'arity': 'binary', 'inplace': False},

    # Bitwise
    '&':   {'callee': (lambda x, y: x & y,),   'arity': 'binary', 'inplace': False},
    '|':   {'callee': (lambda x, y: x | y,),   'arity': 'binary', 'inplace': False},
    '^':   {'callee': (lambda x, y: x ^ y,),   'arity': 'binary', 'inplace': False},
    '<<':  {'callee': (lambda x, y: x << y,),  'arity': 'binary', 'inplace': False},
    '>>':  {'callee': (lambda x, y: x >> y,),  'arity': 'binary', 'inplace': False},
    '~':   {'callee': (lambda x: ~x,),         'arity': 'unary',  'inplace': False},

    # Comparators
    '==':  {'callee': (lambda x, y: x == y,),  'arity': 'binary', 'inplace': False},
    '!=':  {'callee': (lambda x, y: x != y,),  'arity': 'binary', 'inplace': False},
    '<':   {'callee': (lambda x, y: x < y,),   'arity': 'binary', 'inplace': False},
    '<=':  {'callee': (lambda x, y: x <= y,),  'arity': 'binary', 'inplace': False},
    '>':   {'callee': (lambda x, y: x > y,),   'arity': 'binary', 'inplace': False},
    '>=':  {'callee': (lambda x, y: x >= y,),  'arity': 'binary', 'inplace': False},

    # Boolean
    'and': {'callee': (lambda x, y: x and y,), 'arity': 'binary', 'inplace': False},
    'or':  {'callee': (lambda x, y: x or y,),  'arity': 'binary', 'inplace': False},
    'not': {'callee': (lambda x: not x,),      'arity': 'unary',  'inplace': False},

    # Assignment / inplace
    '=':   {'callee': (lambda x: x,),                 'arity': 'assign', 'inplace': False},
    '+=':  {'callee': (lambda x, y: x + y,),   'arity': 'assign', 'inplace': True},
    '-=':  {'callee': (lambda x, y: x - y,),   'arity': 'assign', 'inplace': True},
    '*=':  {'callee': (lambda x, y: x * y,),   'arity': 'assign', 'inplace': True},
    '/=':  {'callee': (lambda x, y: x / y,),   'arity': 'assign', 'inplace': True},
    '//=': {'callee': (lambda x, y: x // y,),  'arity': 'assign', 'inplace': True},
    '%=':  {'callee': (lambda x, y: x % y,),   'arity': 'assign', 'inplace': True},
    '**=': {'callee': (lambda x, y: x ** y,),  'arity': 'assign', 'inplace': True},
    '&=':  {'callee': (lambda x, y: x & y,),   'arity': 'assign', 'inplace': True},
    '|=':  {'callee': (lambda x, y: x | y,),   'arity': 'assign', 'inplace': True},
    '^=':  {'callee': (lambda x, y: x ^ y,),   'arity': 'assign', 'inplace': True},
    '<<=': {'callee': (lambda x, y: x << y,),  'arity': 'assign', 'inplace': True},
    '>>=': {'callee': (lambda x, y: x >> y,),  'arity': 'assign', 'inplace': True},
}


_return_signal: type[_return_signal] = type('_return_signal', (Exception,), {
    "__init__": lambda self, object: setattr(self, 'object', object),
})


class struct: ...  # NOQA: N801


class runner:  # NOQA: N801
    builtins: ClassVar[dict[str, Any]] = {
        'print': print,
        'pprint': pprint,
        'range': range,
        'len': len,
        'max': max,
        'min': min,
        'int': int,
        'float': float,
        'complex': complex,
    }

    def __init__(self, nodes: list[AST]) -> None:
        self.stack: list[dict[str, Any]] = [runner.builtins.copy()]
        self.nodes: deque[AST] = deque(nodes)

    @property
    def environ(self) -> dict[str, Any]:
        return self.stack[-1]

    def _new_struct(self, node: Capsule) -> Callable:
        names: list[str] = [name for name, default in node.fields]
        fields: dict[str, Any] = {name: self._run_node(default) for name, default in node.fields}
        defaults: dict[str, Any] = {name: default for name, default in fields.items() if default is not None}

        def __new__(cls: type[struct], *args: Any, **kwargs: Any) -> Any:
            struct: type[struct] = object.__new__(cls)
            used: set[str] = set()

            for name, arg in zip(names, args):
                object.__setattr__(struct, name, arg)
                used.add(name)

            for name, kwarg in kwargs.items():
                if name not in fields:
                    raise TypeError(f"got unexpected keyword argument {name!r}")
                if name in used:
                    raise TypeError(f'got multiple values for argument {name!r}')
                object.__setattr__(struct, name, kwarg)
                used.add(name)

            for name, default in defaults.items():
                if name in used:
                    continue
                object.__setattr__(struct, name, default)
                used.add(name)

            for name in names:
                if name not in used and name not in defaults:
                    raise TypeError(f"argument {name!r} was not specified")

            return struct

        return dataclass(type(f'{['struct', 'record'][node.frozen]}-{node.name}', (struct,), {  # type: ignore[return-value]
            '__annotations__': dict.fromkeys(names, Any),
            '__new__': __new__,
            '__module__': None,
        }), frozen=node.frozen, slots=True)

    def _new_callable(self, node: LambdaFunction | Function) -> Callable:
        names: list[str] = [name for name, default in node.params]
        params: dict[str, Any] = {name: self._run_node(default) for name, default in node.params}
        defaults: dict[str, Any] = {name: default for name, default in params.items() if default is not None}

        closure: dict[str, Any] = self.environ.copy()
        def callee(*args: Any, **kwargs: Any) -> Any:
            self.stack.append(self.environ.copy() | closure.copy())
            used: set[str] = set()

            for name, arg in zip(names, args):
                self.environ[name] = arg
                used.add(name)

            for name, kwarg in kwargs.items():
                if name not in params:
                    raise TypeError(f"got unexpected keyword argument {name!r}")
                if name in used:
                    raise TypeError(f'got multiple values for argument {name!r}')
                self.environ[name] = kwarg
                used.add(name)


            for name, default in defaults.items():
                if name in used:
                    continue
                self.environ[name] = default
                used.add(name)

            for name in names:
                if name not in used and name not in defaults:
                    raise TypeError(f"argument {name!r} was not specified")

            try:
                if isinstance(node, LambdaFunction):
                    return self._run_node(node.returns)

                for stmt in node.codeblock:
                    try:
                        self._run_node(stmt)
                    except _return_signal as signal:
                        return signal.object
            finally:
                self.stack.pop()

            return None

        callee.__name__ = callee.__qualname__ = getattr(node, 'name', '<lambda>')

        return callee

    def _run_node(self, node: AST | Any | None) -> Any | None:
        if isinstance(node, Return):
            if len(self.stack) == 1:
                raise RuntimeError('return statement outside of function')
            raise _return_signal(self._run_node(node.returns))

        match node:
            case Capsule():
                self.environ[node.name] = self._new_struct(node)
            case Function():
                self.environ[node.name] = self._new_callable(node)
            case ForIn():
                for object in self._run_node(node.iterable):  # type: ignore[union-attr]
                    self._run_node(Assign(op='=', target=node.target, object=AuxExpr(object)))
                    for stmt in node.codeblock:
                        self._run_node(stmt)

                if isinstance(node.target, str):
                    self.environ.pop(node.target)
            case While():
                while self._run_node(node.condition):
                    for stmt in node.codeblock:
                        self._run_node(stmt)
            case IfElse():
                for ifthen in node.ifthens:
                    if not self._run_node(ifthen.condition):
                        continue
                    for stmt in ifthen.codeblock:
                        self._run_node(stmt)
                    break
                else:
                    for stmt in node.otherwise:
                        self._run_node(stmt)

            case Assign():
                if node.op == '=':
                    if isinstance(node.target, str):
                        self.environ[node.target] = self._run_node(node.object)
                    elif isinstance(node.target, MemberAccess):
                        setattr(self._run_node(node.target.target), node.target.member, self._run_node(node.object))
                    elif isinstance(node.target, SubscriptAccess):
                        self._run_node(node.target.target).__setitem__(*map(lambda expr: self._run_node(expr), node.target.subscript), self._run_node(node.object))
                    else:
                        raise TypeError(f"cannot assign to {type(node.target).__name__}")
                else:
                    self._run_node(Assign(
                        op='=',
                        target=node.target,
                        object=BinaryOp(
                            op=node.op.removesuffix('='),
                            operands=(node.target, node.object)
                        )
                    ))

            case Null():
                return None
            case Bool() | Number() | String() | AuxExpr():
                return node.object
            case List():
                return list(map(lambda expr: self._run_node(expr), node.object))
            case Dict():
                return dict(map(lambda expr: (self._run_node(expr[0]), self._run_node(expr[1])), node.object))
            case str():
                return self.environ[node]
            case MemberAccess():
                return getattr(self._run_node(node.target), node.member)
            case SubscriptAccess():
                return self._run_node(node.target).__getitem__(*map(lambda expr: self._run_node(expr), node.subscript))  # type: ignore[attr-defined]
            case SubscriptAccess.Slice():
                return slice(self._run_node(node.start), self._run_node(node.stop), self._run_node(node.step))  # type: ignore[arg-type]
            case Call():
                return self._run_node(node.callee)(
                    *list(map(lambda expr: self._run_node(expr), node.args)),
                    **dict(map(lambda expr: (self._run_node(expr[0]), self._run_node(expr[1])), node.kwargs))
                )
            case UnaryOp():
                return operators[node.op]['callee'][0](self._run_node(node.operand))
            case BinaryOp():
                return operators[node.op]['callee'][-1](*map(lambda expr: self._run_node(expr), node.operands))
            case TernaryOp():
                return self._run_node(node.if_true) if self._run_node(node.condition) else self._run_node(node.if_false)
            case LambdaFunction():
                return self._new_callable(node)
            case GroupedExpr():
                return self._run_node(node.expr)

        return node

    def run(self) -> None:
        while self.nodes:
            self._run_node(self.nodes.popleft())


def run(source: str) -> None:
    runner(parser.run(source)).run()

test = lambda x: lambda y: (x + y) * z
z = 10
