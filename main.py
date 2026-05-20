from rich import print

import slx.runner

if __name__ == '__main__':
    with open('src/fft.slx') as stream:
        print("Running FFT")
        slx.runner.run(stream.read())
    print()

    with open('src/fft-updated.slx') as stream:
        print("Running FFT-UPDATED")
        slx.runner.run(stream.read())
    print()

    with open('src/ntt.slx') as stream:
        print("Running NTT")
        slx.runner.run(stream.read())
    print()

    with open('src/ntt-updated.slx') as stream:
        print("Running NTT-UPDATED")
        slx.runner.run(stream.read())
    print()

    print("(All times are expressed in seconds)")
