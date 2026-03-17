from core.runner import run

with open('src/main.slx') as stream:
    source: str = stream.read()

run(source)
