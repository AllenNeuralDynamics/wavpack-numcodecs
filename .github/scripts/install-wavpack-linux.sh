#!/bin/bash

# Check if WAVPACK_VERSION argument is provided
if [ -z "$1" ]; then
    echo "Error: WAVPACK_VERSION argument is required."
    exit 1
else
    WAVPACK_VERSION=$1
fi

# Check if TARGET_FOLDER argument is provided
if [ -z "$2" ]; then
    TARGET_FOLDER=$(pwd)
else
    TARGET_FOLDER=$2
    mkdir -p "$TARGET_FOLDER"
fi

CWD=$(pwd)
cd "$TARGET_FOLDER"

echo "Installing WavPack $WAVPACK_VERSION into $TARGET_FOLDER - CWD: $CWD"

sudo apt update
sudo apt install wget
sudo apt install -y gettext

wget "https://www.wavpack.com/wavpack-${WAVPACK_VERSION}.tar.bz2"
tar -xf wavpack-$WAVPACK_VERSION.tar.bz2
cd wavpack-$WAVPACK_VERSION
./configure
sudo make install
cd ..

echo "WavPack $WAVPACK_VERSION installed into $TARGET_FOLDER Changing directory to: $CWD"
cd "$CWD"
