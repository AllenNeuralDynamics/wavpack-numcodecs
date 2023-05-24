global num_global_encoding_threads
global num_global_decoding_threads
num_global_encoding_threads = None
num_global_decoding_threads = None


def set_num_encoding_threads(num_encoding_threads):
    global num_global_encoding_threads
    num_global_encoding_threads = int(num_encoding_threads)


def get_num_encoding_threads():
    global num_global_encoding_threads
    return num_global_encoding_threads


def reset_num_encoding_threads():
    global num_global_encoding_threads
    num_global_encoding_threads = None


def set_num_decoding_threads(num_decoding_threads):
    global num_global_decoding_threads
    num_global_decoding_threads = int(num_decoding_threads)


def get_num_decoding_threads():
    global num_global_decoding_threads
    return num_global_decoding_threads


def reset_num_decoding_threads():
    global num_global_decoding_threads
    num_global_decoding_threads = None
