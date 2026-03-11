import re
from collections.abc import Iterable
from typing import Callable

from funcparserlib.lexer import *

from .keywords import kwlist

IgnoreRE: str = r'([ \f\t]|\\?\n|#[^\n]*)+'

Double3: str = r'\"\"\"[^\"\\]*(?:(?:\\.|\"(?!\"\"))[^\"\\]*)*\"\"\"'
Single3: str = r'\'\'\'[^\'\\]*(?:(?:\\.|\'(?!\'\'))[^\'\\]*)*\'\'\''
Double: str = r"\"[^\n\"\\]*(?:\\.[^\n\"\\]*)*\""
Single: str = r"\'[^\n\'\\]*(?:\\.[^\n\'\\]*)*\'"
StringRE: str = r'(?:%s)' % '|'.join((Double3, Single3, Double, Single))

HexNumber: str = r'0[xX](?:_?[0-9a-fA-F])+'
OctNumber: str = r'0[oO](?:_?[0-7])+'
BinNumber: str = r'0[bB](?:_?[0-1])+'
DecNumber: str = r'(?:0(?:_?0)*|[1-9](?:_?[0-9])*)'
IntNumber: str = r'(?:%s)' % '|'.join((HexNumber, OctNumber, BinNumber, DecNumber))
Exponent: str = r'[eE][-+]?[0-9](?:_?[0-9])*'
PointFloat: str = r'(?:%s)' % '|'.join((r'[0-9](?:_?[0-9])*\.(?:[0-9](?:_?[0-9])*)?', r'\.[0-9](?:_?[0-9])*')) + r'(?:%s)?' % Exponent
ExpFloat: str = r'[0-9](?:_?[0-9])*' + Exponent
FloatNumber: str = r'(?:%s)' % '|'.join((PointFloat, ExpFloat))
ImagNumber: str = r'(?:%s)' % '|'.join((r'[0-9](?:_?[0-9])*[jJ]', FloatNumber + r'[jJ]'))
NumberRE: str = r'(?:%s)' % '|'.join((ImagNumber, FloatNumber, IntNumber))

SymbolRE: str = '(?:%s)' % '|'.join(map(re.escape, sorted({
    '(', ')', '[', ']', '{', '}',

    '.', ',', ';', ':', '?',

    '+', '-', '*', '/', '%', '**',

    '->',

    '==', '!=', '<', '<=', '>', '>=',

    '<<', '>>', '&', '|', '~', '^',

    '='
}, key=len, reverse=True)))

NameRE: str = r'[^\W\d]\w*'

specs: list[TokenSpec] = [
    TokenSpec('IGNORE', IgnoreRE),
    TokenSpec('STRING', StringRE),
    TokenSpec('NUMBER', NumberRE),
    TokenSpec('SYMBOL', SymbolRE),
    TokenSpec('NAME', NameRE),
]

def lexer(source: str) -> list[Token]:
    tokenizer: Callable[[str], Iterable[Token]] = make_tokenizer(specs)
    tokens: list[Token] = []

    for token in tokenizer(source):
        if token.type == 'IGNORE':
            continue
        if token.value in kwlist:
            tokens.append(Token('KEYWORD', token.value, token.start, token.end))
        else:
            tokens.append(token)

    return tokens
