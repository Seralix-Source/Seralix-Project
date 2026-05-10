from rich.pretty import pprint

import slx.runner

if __name__ == '__main__':
    with open('src/fft.slx') as stream:
        pprint("Running FFT")
        slx.runner.run(stream.read())
    with open('src/fft-updated.slx') as stream:
        pprint("Running FFT-UPDATED")
        slx.runner.run(stream.read())
    with open('src/ntt.slx') as stream:
        pprint("Running NTT")
        slx.runner.run(stream.read())
    with open('src/ntt-updated.slx') as stream:
        pprint("Running NTT-UPDATED")
        slx.runner.run(stream.read())
