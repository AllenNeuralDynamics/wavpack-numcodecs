"""Process-wide default thread counts, used by codecs created without explicit ones."""

num_global_encoding_threads = None
num_global_decoding_threads = None


def set_num_encoding_threads(num_encoding_threads):
    """Set the default number of encoding threads."""
    global num_global_encoding_threads
    num_global_encoding_threads = int(num_encoding_threads)


def get_num_encoding_threads():
    """Return the default number of encoding threads, or None if unset."""
    return num_global_encoding_threads


def reset_num_encoding_threads():
    """Unset the default number of encoding threads."""
    global num_global_encoding_threads
    num_global_encoding_threads = None


def set_num_decoding_threads(num_decoding_threads):
    """Set the default number of decoding threads."""
    global num_global_decoding_threads
    num_global_decoding_threads = int(num_decoding_threads)


def get_num_decoding_threads():
    """Return the default number of decoding threads, or None if unset."""
    return num_global_decoding_threads


def reset_num_decoding_threads():
    """Unset the default number of decoding threads."""
    global num_global_decoding_threads
    num_global_decoding_threads = None
