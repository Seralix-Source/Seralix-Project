from core.runner import runner

with open('src/fft.slx') as stream:
    print("RUNNING FFT")
    runner(stream.read()).run()


with open('src/ntt.slx') as stream:
    print("RUNNING NTT")
    runner(stream.read()).run()
