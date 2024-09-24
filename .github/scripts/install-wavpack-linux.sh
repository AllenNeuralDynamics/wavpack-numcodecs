#!/bin/bash

# Check if TARGET_FOLDER argument is provided
if [ -n "$1" ]; then
    TARGET_FOLDER=$1
    # Create the target folder if it doesn't exist
    mkdir -p "$TARGET_FOLDER"
    # Change directory to the target folder
    cd "$TARGET_FOLDER"
fi

sudo apt update
sudo apt install wget
sudo apt install -y gettext

WAVPACK_LATEST_VERSION="$(cat ./.github/wavpack_latest_version.txt)"

wget "https://www.wavpack.com/wavpack-$WAVPACK_LATEST_VERSION.tar.bz2"
tar -xf wavpack-$WAVPACK_LATEST_VERSION.tar.bz2
cd wavpack-$WAVPACK_LATEST_VERSION
./configure
sudo make install
cd ..