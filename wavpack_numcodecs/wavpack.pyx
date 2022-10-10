# cython: embedsignature=True
# cython: profile=False
# cython: linetrace=False
# cython: binding=False
# cython: language_level=3


from cpython.buffer cimport PyBUF_ANY_CONTIGUOUS, PyBUF_WRITEABLE
from cpython.bytes cimport PyBytes_FromStringAndSize, PyBytes_AS_STRING


from .compat_ext cimport Buffer
from .compat_ext import Buffer

import numcodecs
from numcodecs.compat import ensure_contiguous_ndarray
from numcodecs.abc import Codec

from pathlib import Path
import numpy as np

# controls the size of destination buffer for decompression
DECOMPRESSION_BUFFER_MULTIPLIER = 50


cdef extern from "wavpack/wavpack_local.h":
    const char* WavpackGetLibraryVersionString()

cdef extern from "src/encoder.c":
    size_t WavpackEncodeFile (void *source, size_t num_samples, size_t num_chans, int level, float bps, void *destin, 
                              size_t destin_bytes, int dtype)

cdef extern from "src/decoder.c":
    size_t WavpackDecodeFile (void *source, size_t source_bytes, int *num_chans, int *bytes_per_sample, void *destin, 
                              size_t destin_bytes)


VERSION_STRING = WavpackGetLibraryVersionString()
VERSION_STRING = str(VERSION_STRING, 'ascii')
__version__ = VERSION_STRING


dtype_enum = {
    "int8": 0,
    "int16": 1,
    "int32": 2,
    "float32": 3
}


def compress(source, int level, int num_samples, int num_chans, float bps, int dtype):
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


    # setup source buffer
    source_buffer = Buffer(source, PyBUF_ANY_CONTIGUOUS)
    source_ptr = source_buffer.ptr
    source_size = source_buffer.nbytes

    try:

        # setup destination
        dest = PyBytes_FromStringAndSize(NULL, source_size)
        dest_ptr = PyBytes_AS_STRING(dest)
        dest_size = source_size

        compressed_size = WavpackEncodeFile(source_ptr, num_samples, num_chans, level, bps, dest_ptr, dest_size, dtype)

    finally:

        # release buffers
        source_buffer.release()

    # check compression was successful
    if compressed_size == -1:
        raise RuntimeError(f'WavPack compression error: {compressed_size}')

    # resize after compression
    dest = dest[:compressed_size]

    return dest


def decompress(source, dest=None):
    """Decompress data.

    Parameters
    ----------
    source : bytes-like
        Compressed data. Can be any object supporting the buffer protocol.
    dest : array-like, optional
        Object to decompress into.

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

    # setup source buffer
    source_buffer = Buffer(source, PyBUF_ANY_CONTIGUOUS)
    source_ptr = source_buffer.ptr
    source_size = source_buffer.nbytes

    try:
        # setup destination
        if dest is None:
            # allocate memory
            dest_size = source_size * DECOMPRESSION_BUFFER_MULTIPLIER * max_bytes_per_sample
            dest = PyBytes_FromStringAndSize(NULL, dest_size)
            dest_ptr = PyBytes_AS_STRING(dest)
        else:
            arr = ensure_contiguous_ndarray(dest)
            dest_buffer = Buffer(arr, PyBUF_ANY_CONTIGUOUS | PyBUF_WRITEABLE)
            dest_ptr = dest_buffer.ptr
            dest_size = dest_buffer.nbytes

        decompressed_samples = WavpackDecodeFile(source_ptr, source_size, num_chans_ptr, bytes_per_sample_ptr, 
                                                 dest_ptr, dest_size)

    finally:

        # release buffers
        source_buffer.release()
        if dest_buffer is not None:
            dest_buffer.release()

    # check decompression was successful
    if decompressed_samples <= 0:
        raise RuntimeError(f'WavPack decompression error: {decompressed_samples}')

    return dest[:decompressed_samples * num_chans * bytes_per_sample]


        
class WavPack(Codec):    
    codec_id = "wavpack"
    max_block_size = 131072
    supported_dtypes = ["int8", "int16", "int32", "float32"]
    max_channels = 4096
    max_buffer_size = 0x7E000000

    def __init__(self, level=1, bps=None):
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
        
    def get_config(self):
        # override to handle encoding dtypes
        return dict(
            id=self.codec_id,
            level=self.level,
            bps=float(self.bps)
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
        return compress(data, self.level, nsamples, nchans, self.bps, dtype_id)

    def decode(self, buf, out=None):        
        buf = ensure_contiguous_ndarray(buf, self.max_buffer_size)
        return decompress(buf, out)


numcodecs.register_codec(WavPack)
