# WavPack - numcodecs implementation

[Numcodecs](https://numcodecs.readthedocs.io/en/latest/index.html) wrapper to the 
[WavPack](https://www.wavpack.com/index.html) audio codec.

This implementation enables one to use WavPack as a compressor in 
[Zarr](https://zarr.readthedocs.io/en/stable/index.html).

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