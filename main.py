from rich.pretty import pprint

from core.parser import parser

with open('src/main.slx') as stream:
    source: str = stream.read()

pprint(parser(source))
