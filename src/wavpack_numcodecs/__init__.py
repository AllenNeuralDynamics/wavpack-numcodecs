import importlib.metadata
import importlib.util
import numcodecs
from packaging.version import parse

from wavpack_numcodecs.wavpack import wavpack_version


HAVE_ZARR = importlib.util.find_spec("zarr") is not None

USE_ZARR_V3 = False
if HAVE_ZARR:
    import zarr

    if parse(zarr.__version__) >= parse("3.0.0"):
        USE_ZARR_V3 = True
    
if USE_ZARR_V3:
    from numcodecs import register_codec
    from wavpack_numcodecs.wavpack import WavPack
else:
    from zarr.registry import register_codec
    from wavpack_numcodecs.wavpackv3 import WavPack

register_codec("wavpack", WavPack)

from .globals import (
    get_num_decoding_threads,
    get_num_encoding_threads,
    reset_num_decoding_threads,
    reset_num_encoding_threads,
    set_num_decoding_threads,
    set_num_encoding_threads,
)

__version__ = importlib.metadata.version("wavpack_numcodecs")
