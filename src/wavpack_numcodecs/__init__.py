from wavpack_numcodecs.wavpack import WavPack, wavpack_version

from .globals import (
    get_num_decoding_threads,
    get_num_encoding_threads,
    reset_num_decoding_threads,
    reset_num_encoding_threads,
    set_num_decoding_threads,
    set_num_encoding_threads,
)
import importlib.metadata

__version__ = importlib.metadata.version("wavpack_numcodecs")