# -*- coding: utf-8 -*-
import platform
import shutil
from pathlib import Path
from subprocess import check_output

from setuptools import Extension, setup

try:
    from Cython.Build import cythonize
    from Cython.Distutils import build_ext
except ImportError:
    have_cython = False
else:
    have_cython = True

LATEST_WAVPACK_VERSION = "5.7.0"
SRC_FOLDER = "src/wavpack_numcodecs"


def get_build_extensions():
    include_dirs = [f"{SRC_FOLDER}/include"]
    runtime_library_dirs = []
    extra_link_args = []

    if platform.system() == "Linux":
        libraries = ["wavpack"]
        if shutil.which("wavpack") is not None:
            out = check_output(["wavpack", "--version"])
            print(f"WavPack is installed!\n{out.decode()}")
            extra_link_args = ["-L/usr/local/lib/", "-L/usr/bin/"]
            runtime_library_dirs = ["/usr/local/lib/", "/usr/bin/"]
        else:
            print("Using shipped libraries")
            wavpack_libraries_folder = Path(f"{SRC_FOLDER}/libraries/{LATEST_WAVPACK_VERSION}")
            available_glibc_builds = [
                p.name for p in wavpack_libraries_folder.iterdir() if p.is_dir() and "linux" in p.name
            ]
            available_glibc_versions = [
                p[p.find("glibc") + len("glibc") :] for p in available_glibc_builds
            ]

            glibc_version = platform.libc_ver()[1]
            if glibc_version not in available_glibc_versions:
                raise RuntimeError(
                    f"Could not find a matching glibc version for the shipped libraries. "
                    f"Available builds: {available_glibc_versions}"
                )
            distr_folder = f"linux-x86_64-glibc{glibc_version}"

            extra_link_args = [f"-L{wavpack_libraries_folder}/{distr_folder}"]
            runtime_library_dirs = [
                f"$ORIGIN/libraries/{LATEST_WAVPACK_VERSION}/{distr_folder}",
            ]
            # hack
            shutil.copy(
                f"{wavpack_libraries_folder}/{distr_folder}/libwavpack.so",
                f"{wavpack_libraries_folder}/{distr_folder}/libwavpack.so.1",
            )
    elif platform.system() == "Darwin":
        libraries = ["wavpack"]
        assert shutil.which("wavpack") is not None, (
            f"WavPack needs to be installed externally for MacOS platforms.\n"
            f"You can use homebrew: \n\t >>> brew install wavpack\nor compile it from source:"
            f"\n\t >>> wget https://www.wavpack.com/wavpack-{LATEST_WAVPACK_VERSION}.tar.bz2"
            f"\n\t >>> tar -xf wavpack-{LATEST_WAVPACK_VERSION}.tar.bz2"
            f"\n\t >>> cd wavpack-{LATEST_WAVPACK_VERSION}\n\t >>> ./configure\n\t >>> sudo make install\n\t >>> cd .."
        )
        print("wavpack is installed!")
        extra_link_args = ["-L~/include/", "-L/usr/local/include/", "-L/usr/include"]
        runtime_library_dirs = ["/opt/homebrew/lib/", "/opt/homebrew/Cellar"]
        for rt_dir in runtime_library_dirs:
            extra_link_args.append(f"-L{rt_dir}")
    else:  # windows
        libraries = ["wavpackdll"]
        # add library folder to PATH and copy .dll in the src
        if "64" in platform.architecture()[0]:
            lib_path = f"{SRC_FOLDER}/libraries/{LATEST_WAVPACK_VERSION}/windows-x86_64"
        else:
            lib_path = f"{SRC_FOLDER}/libraries/{LATEST_WAVPACK_VERSION}/windows-x86_32"
        extra_link_args = [f"/LIBPATH:{lib_path}"]
        for libfile in Path(lib_path).iterdir():
            shutil.copy(libfile, SRC_FOLDER)

    if have_cython:
        print("Building with Cython")
        sources_compat_ext = [f"{SRC_FOLDER}/compat_ext.pyx"]
        sources_wavpack_ext = [f"{SRC_FOLDER}/wavpack.pyx"]
    else:
        sources_compat_ext = [f"{SRC_FOLDER}/compat_ext.c"]
        sources_wavpack_ext = [f"{SRC_FOLDER}/wavpack.c"]

    extensions = [
        Extension("wavpack_numcodecs.compat_ext", sources=sources_compat_ext, extra_compile_args=[]),
        Extension(
            "wavpack_numcodecs.wavpack",
            sources=sources_wavpack_ext,
            include_dirs=include_dirs,
            libraries=libraries,
            extra_link_args=extra_link_args,
            runtime_library_dirs=runtime_library_dirs,
        ),
    ]

    if have_cython:
        extensions = cythonize(extensions)

    return extensions


entry_points = {"numcodecs.codecs": ["wavpack = wavpack_numcodecs:WavPack"]}
extensions = get_build_extensions()
cmdclass = {"build_ext": build_ext} if have_cython else {}

setup(
    ext_modules=extensions,
    cmdclass=cmdclass,
    entry_points=entry_points,
)
