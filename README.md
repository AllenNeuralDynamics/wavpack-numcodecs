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
[recent version Wavpack version](https://github.com/dbry/WavPack/releases/tag/5.7.0).

On Linux, if an existing `wavpack` installation is found, the package will use it. Otherwise, it will use the pre-built binaries available in the `wavpack_numcodecs/libraries` folder.

On Windows, you need to have the "Microsoft C++ Build Tools" installed. You can download it and install it from [here](https://visualstudio.microsoft.com/visual-cpp-build-tools/).

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

# Developmers guide

## How to upgrade WavPack installation and make a new release

To upgrade the WavPack installation, you need to:

1. Download the latest version of WavPack from the [official website](https://www.wavpack.com/downloads.html).
2. Extract the content of the downloaded file.
3. Create a new folder in the `src/wavpack_numcodecs/libraries` folder with the name of the version of the WavPack you are installing.
4. Add the Windows .dll and .lib files to the `windows-x86_32` and `windows-x86_64` folders, respectievely.
5. Update the version of the CI workflows in the `.github/wavpack_latest_version.txt` file and set the `LATEST_WAVPACK_VERSION` variable in the `setup.py` to match the version of the WavPack you are installing.
6. Make a PR with the changes and merge it.
7. Manually trigger the `Build wavpack binaries` workflow in the Actions tab of the repository. This will automatically build the binaries for different Linux versions and make PRs with the changes to the `main` branch.
8. Merge the automated PRs to update the Linux binaries.
9. Update the version of the package in the `pyproject.toml` file and tag the repo to automatically make a new release.
