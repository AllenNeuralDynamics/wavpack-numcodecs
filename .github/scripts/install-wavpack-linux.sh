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

sudo apt-get update
# autoconf/automake/libtool are only needed by the git-tag fallback below, which
# ships configure.ac instead of a generated configure script.
sudo apt-get install -y wget gettext autoconf automake libtool

# www.wavpack.com sits behind a WAF that sporadically rejects plain GETs: it
# either answers "415 Unsupported Media Type" or, worse, answers 200 OK with an
# HTML error page in place of the tarball. Retry on the error codes, validate
# the payload, and fall back to other sources. The last mirror is the git tag
# archive, which has no pre-generated configure script (see autogen.sh below).
MIRRORS=(
    "https://www.wavpack.com/wavpack-${WAVPACK_VERSION}.tar.bz2"
    "https://www.wavpack.com/wavpack-${WAVPACK_VERSION}.tar.xz"
    "https://github.com/dbry/WavPack/archive/refs/tags/${WAVPACK_VERSION}.tar.gz"
)

# Kept as "wavpack-<version>": build-wavpack-binaries.yml looks for the compiled
# library under $TARGET_FOLDER/wavpack-<version>/src/.libs.
SRC_DIR="$TARGET_FOLDER/wavpack-${WAVPACK_VERSION}"
rm -rf "$SRC_DIR"
mkdir -p "$SRC_DIR"

downloaded=0
for url in "${MIRRORS[@]}"; do
    archive="$TARGET_FOLDER/$(basename "$url")"
    echo "Attempting download from: $url"
    if ! wget --tries=5 --waitretry=10 --retry-connrefused \
            --retry-on-http-error=415,429,500,502,503,504 \
            --header="User-Agent: Mozilla/5.0" \
            -O "$archive" "$url"; then
        echo "Download failed from $url, trying next mirror..."
        continue
    fi
    # A 200 OK is not enough: make sure we got an archive and not an HTML page.
    if ! tar -tf "$archive" > /dev/null 2>&1; then
        echo "Downloaded file from $url is not a valid tar archive:"
        file "$archive" || true
        head -c 200 "$archive" || true
        echo
        echo "Trying next mirror..."
        continue
    fi
    # --strip-components=1 normalizes the differing top-level directory names
    # ("wavpack-<version>" for releases, "WavPack-<version>" for git tags).
    tar -xf "$archive" -C "$SRC_DIR" --strip-components=1
    downloaded=1
    break
done

if [ "$downloaded" -ne 1 ]; then
    echo "Error: failed to download WavPack $WAVPACK_VERSION from all mirrors."
    exit 1
fi

cd "$SRC_DIR"
if [ ! -f ./configure ]; then
    echo "No configure script found (git-tag archive), generating one..."
    NOCONFIGURE=1 ./autogen.sh
fi
./configure
sudo make install
sudo ldconfig

echo "WavPack $WAVPACK_VERSION installed into $TARGET_FOLDER Changing directory to: $CWD"
cd "$CWD"
