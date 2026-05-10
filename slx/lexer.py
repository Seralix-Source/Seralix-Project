import re
from token import EXACT_TOKEN_TYPES
from tokenize import Number, String, group  # NOQA: Not inteded to be imported

import funcparserlib.lexer
from funcparserlib.lexer import Token, TokenSpec


def run(source: str) -> list[Token]:
    specs: list[TokenSpec] = [
        TokenSpec("IGNORE", r"[ \f\t\r\n]+|#[^\n]*"),
        TokenSpec("NUMBER", Number),
        TokenSpec("STRING", String),
        TokenSpec("OP", group(*map(re.escape, sorted({'?'}.union(EXACT_TOKEN_TYPES), key=len, reverse=True)))),
        TokenSpec("NAME", r"[^\W\d]\w*"),
    ]
    tokens: list[Token] = []
    for token in funcparserlib.lexer.make_tokenizer(specs)(source):
        if token.type == "IGNORE":
            continue
        tokens.append(token)
    return tokens
