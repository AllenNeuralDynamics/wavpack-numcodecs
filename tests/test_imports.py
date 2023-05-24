def test_imports():
    from wavpack_numcodecs import wavpack_version

    print(f"\nWavpack library verison: {wavpack_version}")
    from wavpack_numcodecs import WavPack

    wv0 = WavPack(level=2)
    print(wv0)
    wv3 = WavPack(level=2, bps=3)
    print(wv3)


def test_global_settings():
    from wavpack_numcodecs import (
        WavPack,
        get_num_decoding_threads,
        get_num_encoding_threads,
        reset_num_decoding_threads,
        reset_num_encoding_threads,
        set_num_decoding_threads,
        set_num_encoding_threads,
    )

    set_num_decoding_threads(4)
    set_num_encoding_threads(2)

    assert get_num_decoding_threads() == 4
    assert get_num_encoding_threads() == 2

    wv = WavPack(num_encoding_threads=4, num_decoding_threads=2)
    assert wv.num_encoding_threads == get_num_encoding_threads()
    assert wv.num_decoding_threads == get_num_decoding_threads()

    reset_num_encoding_threads()
    reset_num_decoding_threads()

    wv = WavPack(num_encoding_threads=4, num_decoding_threads=2)
    assert wv.num_encoding_threads == 4
    assert wv.num_decoding_threads == 2
