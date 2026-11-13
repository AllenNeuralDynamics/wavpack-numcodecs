[![PyPI version](https://badge.fury.io/py/wavpack-numcodecs.svg)](https://badge.fury.io/py/wavpack-numcodecs) ![tests](https://github.com/AllenNeuralDynamics/wavpack-numcodecs/actions/workflows/build.yml/badge.svg)


# WavPack - numcodecs implementation

[Numcodecs](https://numcodecs.readthedocs.io/en/latest/index.html) wrapper to the 
[WavPack](https://www.wavpack.com/index.html) audio codec.

This implementation enables one to use WavPack as a compressor in 
[Zarr](https://zarr.readthedocs.io/en/stable/index.html).


## Installation

```
pip install wavpack-numcodecs
```

Wheels are published for Linux (x86_64 and aarch64, glibc 2.17 or newer), macOS (arm64 and x86_64) and Windows
(x86_64), for CPython 3.11 and later. Each wheel has WavPack built in, so nothing else needs installing.

### Building from source

Where no wheel fits, pip builds the package from the source distribution, which needs a C compiler and CMake. The
build links a system WavPack (5.6.4 or newer) if `pkg-config` finds one, and otherwise compiles the copy of WavPack
included in the source distribution.

To build from a clone, fetch the WavPack submodule first:

```
git clone --recurse-submodules https://github.com/AllenNeuralDynamics/wavpack-numcodecs.git
cd wavpack-numcodecs
pip install .
```

The CMake option `WAVPACK_NUMCODECS_WAVPACK` chooses the WavPack to link:

| Value | Links |
|---|---|
| `AUTO` (default) | a system WavPack >= 5.6.4 found by `pkg-config`, otherwise the bundled one |
| `SYSTEM` | the system WavPack of any version, failing if there is none |
| `BUNDLED` | the bundled WavPack, which the published wheels use |

```
pip install . --config-settings=cmake.define.WAVPACK_NUMCODECS_WAVPACK=SYSTEM
```

## Usage

This is a simple example on how to use the `WavPackCodec` with `zarr`:

```
from wavpack_numcodecs import WavPack

data = ... # any numpy array

# instantiate WavPack compressor
wv_compressor = WavPack(level=2, bps=None)

# v2
group = zarr.group()
z = group.create_dataset(name="wv_dset", data=data, compressor=wv_compressor)

# v3
zarr.config.set({"default_zarr_version": 3})
group = zarr.group()
z = group.create_array(name="wv_dset3", data=data, serializer=wv_compressor)

data_read = z[:]
```
Available `**kwargs` can be browsed with: `WavPack?`

> **_NOTE 1:_**  In order to reload in zarr an array saved with the `WavPack`, you just need to have the `wavpack_numcodecs` package
installed.

> **_NOTE 2:_** The Zarr v3 implementation is an `ArrayBytesCodec`. The `zarr.create_array` function only supports `ArrayArrayCodec` objects for `filters` and `BytesBytesCodecs` for `compressors`. Hence, we need to use the `WavPack` codec as a `serializer`, which is expected to be an `ArrayBytesCodec` object.

# Developers guide

The extension modules are built with [scikit-build-core](https://scikit-build-core.readthedocs.io) and CMake from the
Cython sources in `src/wavpack_numcodecs`. WavPack is pinned as the git submodule `extern/wavpack`.

Run the tests against a local build, and the linters, with:

```
uv run pytest
uv run ruff format
uv run ruff check
uv run codespell
uv run interrogate -v
```

CI runs the same linters before it builds anything.

## Upgrading WavPack

Dependabot proposes new WavPack releases as submodule bumps. To upgrade by hand:

```
git -C extern/wavpack fetch --tags
git -C extern/wavpack checkout <new tag>
git add extern/wavpack
```

## Making a release

Commit messages follow [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/). After CI passes on
`main`, the `Bump version` workflow runs [commitizen](https://commitizen-tools.github.io/commitizen/): a `fix` commit
since the last release bumps the patch version, a `feat` bumps the minor version, and other types bump nothing.
Commitizen updates `pyproject.toml` and `CHANGELOG.md` and pushes the tag, and the tag's `Build, test and publish` run
uploads the release to PyPI. To release changes that bump nothing, such as `build` or `ci` commits, run `Bump version`
from the Actions tab with an increment of PATCH, MINOR or MAJOR.
