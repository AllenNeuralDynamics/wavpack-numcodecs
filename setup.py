# -*- coding: utf-8 -*-
from setuptools import setup, find_packages, Extension
from pathlib import Path
import platform
import shutil


try:
    from Cython.Build import cythonize
    from Cython.Distutils import build_ext
except ImportError:
    have_cython = False
else:
    have_cython = True

print("HAVE_CYTHON", have_cython)


def open_requirements(fname):
    with open(fname, mode='r') as f:
        requires = f.read().split('\n')
    requires = [e for e in requires if len(e) > 0 and not e.startswith('#')]
    return requires


def get_build_extensions():
    include_dirs = ["wavpack_numcodecs/include"]
    runtime_library_dirs = []
    extra_link_args = []

    if platform.system() == "Linux":
        libraries = ["wavpack"]
        if shutil.which("wavpack") is not None:
            print("wavpack is installed!")
            extra_link_args = ["-L/usr/local/lib/", "-L/usr/bin/"]
            runtime_library_dirs = ["/usr/local/lib/", "/usr/bin/"]
        else:
            print("Using shipped libraries")
            extra_link_args = [f"-Lwavpack_numcodecs/libraries/linux-x86_64"]
            runtime_library_dirs = ["$ORIGIN/libraries/linux-x86_64"]
            # hack
            shutil.copy("wavpack_numcodecs/libraries/linux-x86_64/libwavpack.so",
                        "wavpack_numcodecs/libraries/linux-x86_64/libwavpack.so.1")
    elif platform.system() == "Darwin":
        libraries = ["wavpack"]
        assert shutil.which("wavpack") is not None, ("wavpack need to be installed externally. "
                                                     "You can use: brew install wavpack")
        print("wavpack is installed!")
        extra_link_args = ["-L~/include/", "-L/usr/local/include/", "-L/usr/include"]
    else:  # windows
        libraries = ["wavpackdll"]
        # add library folder to PATH and copy .dll in the src
        if "64" in platform.architecture()[0]:
            lib_path = "wavpack_numcodecs/libraries/windows-x86_64"
        else:
            lib_path = "wavpack_numcodecs/libraries/windows-x86_32"
        extra_link_args = [f"/LIBPATH:{lib_path}"]
        for libfile in Path(lib_path).iterdir():
            shutil.copy(libfile, "wavpack_numcodecs")

    if have_cython:
        sources_compat_ext = ['wavpack_numcodecs/compat_ext.pyx']
        sources_wavpack_ext = ["wavpack_numcodecs/wavpack.pyx"]
    else:
        sources_compat_ext = ['wavpack_numcodecs/compat_ext.c']
        sources_wavpack_ext = ["wavpack_numcodecs/wavpack.c"]

    extensions = [
        Extension('wavpack_numcodecs.compat_ext',
                  sources=sources_compat_ext,
                  extra_compile_args=[]),
        Extension('wavpack_numcodecs.wavpack',
                  sources=sources_wavpack_ext,
                  include_dirs=include_dirs,
                  libraries=libraries,
                  extra_link_args=extra_link_args,
                  runtime_library_dirs=runtime_library_dirs
                  ),
    ]

    if have_cython:
        extensions = cythonize(extensions)

    return extensions


d = {}
exec(open("wavpack_numcodecs/version.py").read(), None, d)
version = d['version']
long_description = open("README.md").read()

install_requires = open_requirements('requirements.txt')
entry_points = {"numcodecs.codecs": ["wavpack = wavpack_numcodecs:WavPack"]}
extensions = get_build_extensions()
cmdclass = {'build_ext': build_ext} if have_cython else {}

setup(
    name="wavpack_numcodecs",
    version=version,
    author="Alessio Buccino, David Bryant",
    author_email="alessiop.buccino@gmail.com",
    description="Numcodecs implementation of WavPack audio codec.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/AllenNeuralDynamics/wavpack-numcodecs",
    install_requires=install_requires,
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    packages=find_packages(),
    ext_modules=extensions,
    entry_points=entry_points,
    cmdclass=cmdclass,
    include_package_data=True
)
