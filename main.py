from core.runner import runner

with open('src/main.slx') as stream:
    source: str = stream.read()

runner(source).run()
