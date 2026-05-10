import slx.runner

if __name__ == '__main__':
    with open('src/fft.slx') as stream:
        slx.runner.run(stream.read())
    with open('src/ntt.slx') as stream:
        slx.runner.run(stream.read())
    with open('src/ntt-updated.slx') as stream:
        slx.runner.run(stream.read())
