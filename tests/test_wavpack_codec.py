import warnings

import numpy as np
import pytest
import zarr
from packaging.version import parse

from wavpack_numcodecs import WavPack, wavpack_version

DEBUG = False


if parse(wavpack_version) >= parse("5.6.4"):
    print("Multi-threading available")
    encode_threads = [1, 2]
    decode_threads = [1, 2]
else:
    print("Multi-threading not available")
    encode_threads = [1]
    decode_threads = [1]

dtypes = ["int8", "int16", "int32", "float32"]


@pytest.fixture(scope="module")
def generate_test_data():
    test_signals = {}
    for dtype in dtypes:
        test_signals[dtype] = generate_test_signals(dtype)
    return test_signals


def run_option(data, level, bps, dns, shaping_weight, e_thr, d_thr):
    dtype = data.dtype
    print(
        f"Dtype {dtype} - level {level} - bps {bps} - dns {dns} - shaping_weight {shaping_weight} - "
        f"e. threads {e_thr} - d. threads {d_thr}"
    )
    cod = WavPack(
        level=level,
        bps=bps,
        dynamic_noise_shaping=dns,
        shaping_weight=shaping_weight,
        num_encoding_threads=e_thr,
        num_decoding_threads=d_thr,
    )
    enc = cod.encode(data)
    dec = cod.decode(enc)

    assert len(enc) < len(dec)
    print("CR", len(dec) / len(enc))

    data_dec = np.frombuffer(dec, dtype=dtype).reshape(data.shape)
    # lossless
    if bps is None:
        assert np.all(data_dec == data)


def make_noisy_sin_signals(shape=(30000,), sin_f=100, sin_amp=50, noise_amp=5, sample_rate=30000, dtype="int16"):
    assert isinstance(shape, tuple)
    assert len(shape) <= 3
    if len(shape) == 1:
        y = np.sin(2 * np.pi * sin_f * np.arange(shape[0]) / sample_rate) * sin_amp
        y = y + np.random.randn(shape[0]) * noise_amp
        y = y.astype(dtype)
    elif len(shape) == 2:
        nsamples, nchannels = shape
        y = np.zeros(shape, dtype=dtype)
        for ch in range(nchannels):
            y[:, ch] = make_noisy_sin_signals((nsamples,), sin_f, sin_amp, noise_amp, sample_rate, dtype)
    else:
        nsamples, nchannels1, nchannels2 = shape
        y = np.zeros(shape, dtype=dtype)
        for ch1 in range(nchannels1):
            for ch2 in range(nchannels2):
                y[:, ch1, ch2] = make_noisy_sin_signals((nsamples,), sin_f, sin_amp, noise_amp, sample_rate, dtype)
    return y


def generate_test_signals(dtype):
    test1d = make_noisy_sin_signals(shape=(3001,), dtype=dtype)
    test1d_long = make_noisy_sin_signals(shape=(200000,), dtype=dtype)
    test2d = make_noisy_sin_signals(shape=(3011, 10), dtype=dtype)
    test2d_long = make_noisy_sin_signals(shape=(200001, 20), dtype=dtype)
    test2d_extra = make_noisy_sin_signals(shape=(3000, 300), dtype=dtype)
    test3d = make_noisy_sin_signals(shape=(1003, 5, 5), dtype=dtype)

    return [test1d, test1d_long, test2d, test2d_long, test2d_extra, test3d]


@pytest.mark.numcodecs
@pytest.mark.skipif(parse(wavpack_version) < parse("5.6.4"), reason="Multi-threading not available")
def test_wavpack_multi_threading_enabled():
    # Should NOT warn!
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        wv = WavPack(num_encoding_threads=4, num_decoding_threads=1)
        wv = WavPack(num_encoding_threads=1, num_decoding_threads=4)
        wv = WavPack(num_encoding_threads=4, num_decoding_threads=4)

@pytest.mark.numcodecs
@pytest.mark.skipif(parse(wavpack_version) >= parse("5.6.4"), reason="Multi-threading available")
def test_wavpack_multi_threading_disabled():
    # Should warn!
    with pytest.warns(UserWarning) as w:
        wv = WavPack(num_encoding_threads=4, num_decoding_threads=1)
    with pytest.warns(UserWarning) as w:
        wv = WavPack(num_encoding_threads=1, num_decoding_threads=4)
    with pytest.warns(UserWarning) as w:
        wv = WavPack(num_encoding_threads=4, num_decoding_threads=4)


@pytest.mark.parametrize("dtype", dtypes)
@pytest.mark.parametrize("level", [1, 2, 3, 4])
@pytest.mark.parametrize("bps", [None, 6, 4, 2.25])
@pytest.mark.parametrize("encode_thread", encode_threads)
@pytest.mark.parametrize("decode_thread", decode_threads)
@pytest.mark.numcodecs
def test_wavpack_numcodecs(generate_test_data, level, bps, dtype, encode_thread, decode_thread):
    print(f"\n\nNUMCODECS: testing dtype {dtype}\n\n")

    test_signals = generate_test_data[dtype]
    for test_sig in test_signals:
        print(f"signal shape: {test_sig.shape}")
        run_option(test_sig, bps=bps, level=level, dns=True, shaping_weight=0, e_thr=encode_thread, d_thr=decode_thread)


@pytest.mark.parametrize("dtype", dtypes)
@pytest.mark.parametrize("dns", [False, True])
@pytest.mark.parametrize("shaping_weight", [-0.5, 0, 0.5])
@pytest.mark.numcodecs
def test_wavpack_noise_shaping(generate_test_data, dtype, dns, shaping_weight):
    print(f"\n\nNUMCODECS: testing dtype {dtype}\n\n")

    test_signals = generate_test_data[dtype]
    for test_sig in test_signals:
        print(f"signal shape: {test_sig.shape}")
        run_option(test_sig, bps=2, level=2, dns=dns, shaping_weight=shaping_weight, e_thr=1, d_thr=1)


@pytest.mark.parametrize("dtype", dtypes)
@pytest.mark.parametrize("bps", [None, 3])
@pytest.mark.zarr
def test_wavpack_zarr(generate_test_data, bps, dtype):
    print(f"\n\nZARR: testing dtype {dtype}\n\n")
    test_signals = generate_test_data[dtype]

    for test_sig in test_signals:
        compressor = WavPack(bps=bps)

        print(f"signal shape: {test_sig.shape} - bps: {bps}")
        if test_sig.ndim == 1:
            z = zarr.array(test_sig, chunks=None, compressor=compressor)
            assert z[:].shape == test_sig.shape
            assert z[:100].shape == test_sig[:100].shape
            assert z.nbytes > z.nbytes_stored
            if bps is None:
                np.testing.assert_array_equal(z[:], test_sig)

            z = zarr.array(test_sig, chunks=(1000), compressor=compressor)
            assert z[:].shape == test_sig.shape
            assert z[:100].shape == test_sig[:100].shape
            if bps is None:
                np.testing.assert_array_equal(z[:], test_sig)

        elif test_sig.ndim == 2:
            z = zarr.array(test_sig, chunks=None, compressor=compressor)
            assert z[:].shape == test_sig.shape
            assert z[:100, :10].shape == test_sig[:100, :10].shape
            assert z.nbytes > z.nbytes_stored
            if bps is None:
                np.testing.assert_array_equal(z[:], test_sig)

            z = zarr.array(test_sig, chunks=(1000, None), compressor=compressor)
            assert z[:].shape == test_sig.shape
            assert z[:100, :10].shape == test_sig[:100, :10].shape
            if bps is None:
                np.testing.assert_array_equal(z[:], test_sig)

            z = zarr.array(test_sig, chunks=(None, 10), compressor=compressor)
            assert z[:].shape == test_sig.shape
            assert z[:100, :10].shape == test_sig[:100, :10].shape
            if bps is None:
                np.testing.assert_array_equal(z[:], test_sig)

        else:  # 3d
            z = zarr.array(test_sig, chunks=None, compressor=compressor)
            assert z[:].shape == test_sig.shape
            assert z[:100, :2, :2].shape == test_sig[:100, :2, :2].shape
            assert z.nbytes > z.nbytes_stored
            if bps is None:
                np.testing.assert_array_equal(z[:], test_sig)

            z = zarr.array(test_sig, chunks=(1000, 2, None), compressor=compressor)
            assert z[:].shape == test_sig.shape
            assert z[:100, :2, :2].shape == test_sig[:100, :2, :2].shape
            if bps is None:
                np.testing.assert_array_equal(z[:], test_sig)

            z = zarr.array(test_sig, chunks=(None, 2, 3), compressor=compressor)
            assert z[:].shape == test_sig.shape
            assert z[:100, :2, :2].shape == test_sig[:100, :2, :2].shape
            if bps is None:
                np.testing.assert_array_equal(z[:], test_sig)


if __name__ == "__main__":
    test_wavpack_numcodecs()
    test_wavpack_multi_threading_enabled()
    test_wavpack_multi_threading_disabled()
    test_wavpack_zarr()
