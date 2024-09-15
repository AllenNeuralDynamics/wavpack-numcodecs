# cython: embedsignature=True
# cython: profile=False
# cython: linetrace=False
# cython: binding=False
# cython: language_level=3


from cpython.buffer cimport PyBUF_ANY_CONTIGUOUS, PyBUF_WRITEABLE
from cpython.bytes cimport PyBytes_FromStringAndSize, PyBytes_AS_STRING


from .compat_ext cimport Buffer
from .compat_ext import Buffer

from .globals import get_num_encoding_threads, get_num_decoding_threads

import warnings
import numpy as np
from pathlib import Path
from packaging.version import parse

import numcodecs
from numcodecs.compat import ensure_contiguous_ndarray
from numcodecs.abc import Codec



cdef extern from "wavpack/wavpack.h":
    const char* WavpackGetLibraryVersionString()

cdef extern from "src/encoder.c":
    size_t WavpackEncodeFile (void *source, size_t num_samples, size_t num_chans, int level, float bps, void *destin, 
                              size_t destin_bytes, int dtype, int dynamic_noise_shaping, float shaping_weight,
                              int num_threads) nogil

cdef extern from "src/decoder.c":
    size_t WavpackDecodeFile (void *source, size_t source_bytes, int *num_chans, int *bytes_per_sample, void *destin, 
                              size_t destin_bytes, int num_threads) nogil


VERSION_STRING = WavpackGetLibraryVersionString()
VERSION_STRING = str(VERSION_STRING, 'ascii')
wavpack_version = VERSION_STRING

SUPPORTS_PARALLEL = parse(wavpack_version) >= parse("5.6.4")

dtype_enum = {
    "int8": 0,
    "int16": 1,
    "int32": 2,
    "float32": 3
}


def compress(source, int level, int num_samples, int num_chans, float bps, int dtype,
             int dynamic_noise_shaping, float shaping_weight, int num_encoding_threads):
    """Compress data.

    Parameters
    ----------
    source : bytes-like
        Data to be compressed. Can be any object supporting the buffer
        protocol.
    level : int
        Compression level. The larger the level, the slower the algorithm, but also
        the higher the compression.
    num_samples : int
        Number of samples to compress.
    num_chans : int
        Number of channels to compress.
    bps : float
        Bytes per sample
    dtype : int
        Integer to indicat which dtype the data is ("int8": 0, "int16": 1, "int32": 2, "float32": 3)
    dynamic_noise_shaping : int
        Whether to use dynamic noise shaping
    shaping_weight : float
        The shaping factor
    num_encoding_threads : int
        Number of threads to use for encoding

    Returns
    -------
    dest : bytes
        Compressed data.
    """

    cdef:
        char *source_ptr
        char *dest_ptr
        char *dest_start
        Buffer source_buffer
        unsigned long source_size, dest_size, compressed_size
        bytes dest
        int level_c = level
        int num_samples_c = num_samples
        int num_chans_c = num_chans
        float bps_c = bps
        int dynamic_noise_shaping_c = dynamic_noise_shaping
        float shaping_weight_c = shaping_weight
        int dtype_c = dtype
        int num_threads_c = num_encoding_threads


    # setup source buffer
    source_buffer = Buffer(source, PyBUF_ANY_CONTIGUOUS)
    source_ptr = source_buffer.ptr
    source_size = source_buffer.nbytes

    try:

        # setup destination
        dest = PyBytes_FromStringAndSize(NULL, source_size)
        dest_ptr = PyBytes_AS_STRING(dest)
        dest_size = source_size

        compressed_size = WavpackEncodeFile(source_ptr, num_samples_c, num_chans_c, level_c, bps_c,
                                            dest_ptr, dest_size, dtype_c, dynamic_noise_shaping_c, 
                                            shaping_weight_c, num_threads_c)

    finally:

        # release buffers
        source_buffer.release()

    # check compression was successful
    if compressed_size == -1:
        raise RuntimeError(f'WavPack compression error: {compressed_size}')

    # resize after compression
    dest = dest[:compressed_size]

    return dest


def decompress(source, dest=None, num_decoding_threads=1):
    """Decompress data.

    Parameters
    ----------
    source : bytes-like
        Compressed data. Can be any object supporting the buffer protocol.
    dest : array-like, optional
        Object to decompress into.
    num_decoding_threads : int, optional
        Number of threads to use for decoding, by default 8

    Returns
    -------
    dest : bytes
        Object containing decompressed data.

    """
    cdef:
        char *source_ptr
        char *source_start
        char *dest_ptr
        Buffer source_buffer
        Buffer dest_buffer = None
        unsigned long source_size, dest_size, decompressed_samples
        int num_chans
        int *num_chans_ptr = &num_chans
        int bytes_per_sample
        int *bytes_per_sample_ptr = &bytes_per_sample
        int max_bytes_per_sample = 4
        int num_threads_c = num_decoding_threads

    # setup source buffer
    source_buffer = Buffer(source, PyBUF_ANY_CONTIGUOUS)
    source_ptr = source_buffer.ptr
    source_size = source_buffer.nbytes

    # determine number of samples, num_channels, and bytes_per_sample
    n_decompressed_samples = WavpackDecodeFile(source_ptr, source_size, num_chans_ptr,
                                               bytes_per_sample_ptr, dest_ptr, 0,
                                               num_threads_c)
    try:
        # setup destination
        if dest is None:
            # allocate memory
            dest_size = n_decompressed_samples * num_chans * bytes_per_sample
            dest = PyBytes_FromStringAndSize(NULL, dest_size)
            dest_ptr = PyBytes_AS_STRING(dest)
        else:
            arr = ensure_contiguous_ndarray(dest)
            dest_buffer = Buffer(arr, PyBUF_ANY_CONTIGUOUS | PyBUF_WRITEABLE)
            dest_ptr = dest_buffer.ptr
            dest_size = dest_buffer.nbytes

        with nogil:
            decompressed_samples = WavpackDecodeFile(source_ptr, source_size, num_chans_ptr,
                                                     bytes_per_sample_ptr, dest_ptr, dest_size,
                                                     num_threads_c)

    finally:

        # release buffers
        source_buffer.release()
        if dest_buffer is not None:
            dest_buffer.release()

    # check decompression was successful
    if decompressed_samples <= 0:
        raise RuntimeError(f'WavPack decompression error: {decompressed_samples}')

    return dest


        
class WavPack(Codec):    
    codec_id = "wavpack"
    max_block_size = 131072
    supported_dtypes = ["int8", "int16", "int32", "float32"]
    max_channels = 4096
    max_buffer_size = 0x7E000000

    def __init__(self, level=1, bps=None,
                 dynamic_noise_shaping=True,
                 shaping_weight=0.0,
                 num_encoding_threads=1,
                 num_decoding_threads=8):
        """
        Numcodecs Codec implementation for WavPack (https://www.wavpack.com/) codec.

        2D buffers exceeding the supported number of channels (buffer's second dimension) 
        and buffers > 2D are flattened before compression.


        Parameters
        ----------
        level : int, optional
            The wavpack compression level (from low to high: 1, 2, 3, 4), by default 1
        bps : float or None, optional
            If the bps is not None or 0, the WavPack hybrid mode is used and compression is lossy. 
            The bps is between 2.25 and 24 (it can be a decimal, e.g. 3.5) and it 
            is the average number of bits used to encode each sample, by default None
        dynamic_noise_shaping : bool, optional
            If True, dynamic noise shaping is enabled.
            Dynamic noise shaping is used in hybrid mode (when `bps` is set) and attempts to 
            move the noise up or down in frequency depending on the spectrum of the input, by default True
        shaping_weight : float, optional
            The shaping factor [-1, 1], used if `dynamic_noise_shaping` is False.
            Negative values will move the noise to lower frequencies, positive ones to higher frequencies, 
            by default 0.0
        num_encoding_threads : int, optional
            The number of threads to use during encoding. 
            If using an external parallelization for encoding, 
            it is recommended to use 1, by default 1
        num_decoding_threads : int, optional
            The number of threads to use during decoding, by default 8

        Returns
        -------
        Codec
            The instantiated WavPack numcodecs codec
        """
        self.level = int(level)
        assert self.level in (1, 2, 3, 4)

        if bps is not None:
            if bps > 0:
                self.bps = max(bps, 2.25)
            else:
                self.bps = 0
        else:
            self.bps = 0

        self.dynamic_noise_shaping = dynamic_noise_shaping
        self.shaping_weight = shaping_weight

        if get_num_encoding_threads() is None:
            assert num_encoding_threads >= 0, "num_encoding_threads must be positive!"
        else:
            num_encoding_threads = get_num_encoding_threads()
        if get_num_decoding_threads() is None:
            assert num_decoding_threads >= 0, "num_decoding_threads must be positive!"
        else:
            num_decoding_threads = get_num_decoding_threads()

        if num_encoding_threads > 1 and not SUPPORTS_PARALLEL:
            warnings.warn(
                f"Multi-threading is supported for wavpack version>=5.6.4, "
                f"but current version is {wavpack_version}. Parallel encoding will not be available."
            )
        if num_decoding_threads > 1 and not SUPPORTS_PARALLEL:
            warnings.warn(
                f"Multi-threading is supported for wavpack version>=5.6.4, "
                f"but current version is {wavpack_version}. Parallel decoding will not be available."
            )
        self.num_encoding_threads = int(min(num_encoding_threads, 15))
        self.num_decoding_threads = int(min(num_decoding_threads, 15))

    def get_config(self):
        # override to handle encoding dtypes
        return dict(
            id=self.codec_id,
            level=self.level,
            bps=float(self.bps),
            dynamic_noise_shaping=self.dynamic_noise_shaping,
            shaping_weight=self.shaping_weight,
            num_encoding_threads=self.num_encoding_threads,
            num_decoding_threads=self.num_decoding_threads
        )

    def _prepare_data(self, buf):
        # checks
        assert str(buf.dtype) in self.supported_dtypes, f"Unsupported dtype {buf.dtype}"
        if buf.ndim == 1:
            data = buf[:, None]
        elif buf.ndim == 2:
            _, nchannels = buf.shape
            
            if nchannels > self.max_channels:
                data = buf.flatten()[:, None]    
            else:
                data = buf   
        else:
            data = buf.flatten()[:, None]    
        return data

    def encode(self, buf):
        data = self._prepare_data(buf)
        dtype = str(data.dtype)
        nsamples, nchans = data.shape
        dtype_id = dtype_enum[dtype]
        return compress(data, self.level, nsamples, nchans, self.bps, dtype_id,
                        self.dynamic_noise_shaping, self.shaping_weight, self.num_encoding_threads)

    def decode(self, buf, out=None):        
        buf = ensure_contiguous_ndarray(buf, self.max_buffer_size)
        return decompress(buf, out, self.num_decoding_threads)


numcodecs.register_codec(WavPack)
