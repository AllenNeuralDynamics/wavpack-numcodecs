from wavpack_numcodecs.wavpack import WavPack, wavpack_version

from .globals import (
    get_num_decoding_threads,
    get_num_encoding_threads,
    reset_num_decoding_threads,
    reset_num_encoding_threads,
    set_num_decoding_threads,
    set_num_encoding_threads,
)
from .version import version as __version__
