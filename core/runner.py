from typing import Any

from rich.pretty import pprint

from core.parser import *


def run(source: str) -> None:
    globals: dict[str, Any] = {
        'print': print,
    }

    for node in parser(source):
        pprint(node)
