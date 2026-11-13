cmake_minimum_required(VERSION 3.26...4.3)
project(${SKBUILD_PROJECT_NAME} LANGUAGES C)

# AUTO links a system WavPack found by pkg-config and otherwise builds the pinned submodule; wheels use BUNDLED so
# they never depend on what happens to be installed on the build machine.
set(WAVPACK_NUMCODECS_WAVPACK "AUTO" CACHE STRING "Which WavPack to link: AUTO, SYSTEM or BUNDLED")
set_property(CACHE WAVPACK_NUMCODECS_WAVPACK PROPERTY STRINGS AUTO SYSTEM BUNDLED)

find_package(
  Python
  COMPONENTS Interpreter Development.Module ${SKBUILD_SABI_COMPONENT}
  REQUIRED)
find_package(Cython MODULE REQUIRED VERSION 3.1)
include(UseCython)

set(wavpack_target "")
if(NOT WAVPACK_NUMCODECS_WAVPACK STREQUAL "BUNDLED")
  # AUTO passes over a system WavPack older than 5.6.4, which builds but has no multithreading; SYSTEM takes any.
  if(WAVPACK_NUMCODECS_WAVPACK STREQUAL "AUTO")
    set(wavpack_requirement "wavpack>=5.6.4")
  else()
    set(wavpack_requirement "wavpack")
  endif()
  find_package(PkgConfig QUIET)
  if(PkgConfig_FOUND)
    pkg_check_modules(WAVPACK IMPORTED_TARGET ${wavpack_requirement})
  endif()
  if(WAVPACK_FOUND)
    message(STATUS "Linking system WavPack ${WAVPACK_VERSION}")
    set(wavpack_target PkgConfig::WAVPACK)
  elseif(WAVPACK_NUMCODECS_WAVPACK STREQUAL "SYSTEM")
    message(FATAL_ERROR "WAVPACK_NUMCODECS_WAVPACK=SYSTEM, but pkg-config found no wavpack")
  endif()
endif()

if(NOT wavpack_target)
  set(wavpack_source "${CMAKE_CURRENT_SOURCE_DIR}/extern/wavpack")
  if(NOT EXISTS "${wavpack_source}/CMakeLists.txt")
    message(FATAL_ERROR "extern/wavpack is empty: run `git submodule update --init`, or install WavPack and its "
                        "pkg-config file")
  endif()
  message(STATUS "Building bundled WavPack from extern/wavpack")
  # The static library is linked into a shared extension module, whose only export should be its PyInit function.
  set(CMAKE_POSITION_INDEPENDENT_CODE ON)
  set(CMAKE_C_VISIBILITY_PRESET hidden)
  set(BUILD_SHARED_LIBS OFF)
  set(WAVPACK_ENABLE_THREADS ON CACHE BOOL "" FORCE)
  set(WAVPACK_BUILD_PROGRAMS OFF CACHE BOOL "" FORCE)
  set(WAVPACK_BUILD_DOCS OFF CACHE BOOL "" FORCE)
  add_subdirectory("${wavpack_source}" wavpack EXCLUDE_FROM_ALL)
  # The sources include <wavpack/wavpack.h>, the installed layout; the source tree has include/wavpack.h.
  set(wavpack_header_root "${CMAKE_CURRENT_BINARY_DIR}/wavpack-include")
  configure_file("${wavpack_source}/include/wavpack.h" "${wavpack_header_root}/wavpack/wavpack.h" COPYONLY)
  target_include_directories(wavpack INTERFACE "$<BUILD_INTERFACE:${wavpack_header_root}>")
  set(wavpack_target WavPack::WavPack)
endif()

set(package_dir "${CMAKE_CURRENT_SOURCE_DIR}/src/wavpack_numcodecs")

# Targets are prefixed because the bundled WavPack already defines a target called wavpack.
foreach(module compat_ext wavpack)
  cython_transpile("${package_dir}/${module}.pyx" LANGUAGE C OUTPUT_VARIABLE ${module}_c)
  if(SKBUILD_SABI_VERSION)
    python_add_library(ext_${module} MODULE WITH_SOABI USE_SABI ${SKBUILD_SABI_VERSION} "${${module}_c}")
  else()
    python_add_library(ext_${module} MODULE WITH_SOABI "${${module}_c}")
  endif()
  set_target_properties(ext_${module} PROPERTIES OUTPUT_NAME ${module})
  install(TARGETS ext_${module} DESTINATION wavpack_numcodecs COMPONENT python)
endforeach()

# wavpack.pyx includes src/encoder.c and src/decoder.c from the package directory.
target_include_directories(ext_wavpack PRIVATE "${package_dir}")
target_link_libraries(ext_wavpack PRIVATE ${wavpack_target})
if(wavpack_target STREQUAL "WavPack::WavPack" AND CMAKE_SYSTEM_NAME STREQUAL "Linux")
  # The visibility preset misses the symbols of WavPack's assembly routines.
  target_link_options(ext_wavpack PRIVATE "LINKER:--exclude-libs,ALL")
endif()
