"""WavPack compression for numcodecs and zarr."""

import importlib.metadata
import importlib.util

from packaging.version import parse

from wavpack_numcodecs.globals import (
    get_num_decoding_threads,
    get_num_encoding_threads,
    reset_num_decoding_threads,
    reset_num_encoding_threads,
    set_num_decoding_threads,
    set_num_encoding_threads,
)
from wavpack_numcodecs.wavpack import wavpack_version

HAVE_ZARR = importlib.util.find_spec("zarr") is not None

USE_ZARR_V3 = False
if HAVE_ZARR:
    import zarr

    if parse(zarr.__version__) >= parse("3.0.0"):
        USE_ZARR_V3 = True

if USE_ZARR_V3:
    from zarr.registry import register_codec

    from wavpack_numcodecs.wavpackv3 import WavPack
else:
    from numcodecs import register_codec

    from wavpack_numcodecs.wavpack import WavPack

register_codec("wavpack", WavPack)

__version__ = importlib.metadata.version("wavpack_numcodecs")

__all__ = [
    "WavPack",
    "__version__",
    "get_num_decoding_threads",
    "get_num_encoding_threads",
    "reset_num_decoding_threads",
    "reset_num_encoding_threads",
    "set_num_decoding_threads",
    "set_num_encoding_threads",
    "wavpack_version",
]
