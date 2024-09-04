[![PyPI version](https://badge.fury.io/py/wavpack-numcodecs.svg)](https://badge.fury.io/py/wavpack-numcodecs) ![tests](https://github.com/AllenNeuralDynamics/wavpack-numcodecs/actions/workflows/python-package-cython.yml/badge.svg)


# WavPack - numcodecs implementation

[Numcodecs](https://numcodecs.readthedocs.io/en/latest/index.html) wrapper to the 
[WavPack](https://www.wavpack.com/index.html) audio codec.

This implementation enables one to use WavPack as a compressor in 
[Zarr](https://zarr.readthedocs.io/en/stable/index.html).


### Requirements

To install `wavpack-numcodecs` on MacOS, you need to install `wavpack` with `brew`:

```bash
brew install wavpack
```

For Linux and Windows, the package comes with pre-built binaries of the most 
[recent version Wavpack verison](https://github.com/dbry/WavPack/releases/tag/5.7.0).

On Linux, if an existing `wavpack` installation is found, the package will use it. Otherwise, it will use the pre-built binaries available in the `wavpack_numcodecs/libraries` folder.

## Installation

Install via `pip`:

```
pip install wavpack-numcodecs
```

Or from sources:

```
git clone https://github.com/AllenNeuralDynamics/wavpack-numcodecs.git
cd wavpack_numcodecs
pip install .
```

## Usage

This is a simple example on how to use the `WavPackCodec` with `zarr`:

```
from wavpack_numcodecs import WavPack

data = ... # any numpy array

# instantiate WavPack compressor
wv_compressor = WavPack(level=2, bps=None)

z = zarr.array(data, compressor=wv_compressor)

data_read = z[:]
```
Available `**kwargs` can be browsed with: `WavPack?`

**NOTE:** 
In order to reload in zarr an array saved with the `WavPack`, you just need to have the `wavpack_numcodecs` package
installed.