

def test_imports():
    from wavpack_numcodecs import wavpack_version
    print(f"\nWavpack library verison: {wavpack_version}")
    from wavpack_numcodecs import WavPack
    wv0 = WavPack(level=2)
    print(wv0)
    wv3 = WavPack(level=2, bps=3)
    print(wv3)
