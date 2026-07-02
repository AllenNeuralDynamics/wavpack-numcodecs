#!/bin/bash
set -euo pipefail

# Check if WAVPACK_VERSION argument is provided
if [ -z "${1:-}" ]; then
    echo "Error: WAVPACK_VERSION argument is required."
    exit 1
else
    WAVPACK_VERSION=$1
fi

# Check if TARGET_FOLDER argument is provided
if [ -z "${2:-}" ]; then
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

TARBALL="wavpack-${WAVPACK_VERSION}.tar.bz2"

# www.wavpack.com sporadically returns "415 Unsupported Media Type" for a plain
# GET (WAF/CDN quirk), so retry with backoff and fall back to the identical
# tarball published on GitHub Releases.
MIRRORS=(
    "https://www.wavpack.com/${TARBALL}"
    "https://github.com/dbry/WavPack/releases/download/${WAVPACK_VERSION}/${TARBALL}"
)

downloaded=0
for url in "${MIRRORS[@]}"; do
    echo "Attempting download from: $url"
    if wget --tries=5 --waitretry=10 --retry-connrefused \
            --retry-on-http-error=415,429,500,502,503,504 \
            --header="User-Agent: Mozilla/5.0" \
            -O "$TARBALL" "$url"; then
        downloaded=1
        break
    fi
    echo "Download failed from $url, trying next mirror..."
done

if [ "$downloaded" -ne 1 ]; then
    echo "Error: failed to download $TARBALL from all mirrors."
    exit 1
fi

tar -xf wavpack-$WAVPACK_VERSION.tar.bz2
cd wavpack-$WAVPACK_VERSION
./configure
sudo make install
cd ..

echo "WavPack $WAVPACK_VERSION installed into $TARGET_FOLDER Changing directory to: $CWD"
cd "$CWD"
