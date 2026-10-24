#!/bin/bash
#
# Build lessbrokenssh for classic Mac OS inside the Retro68 container.
#
# usage:
#   ./build.sh [target...]   build into dist/; targets are 68020 68030 68040
#                            601 g3 all (default: all)
#   ./build.sh glyphs        regenerate glyphs and previews (see tools/glyphs/)
#   ./build.sh shell    open a shell in the build environment
#   ./build.sh image    (re)build the container image only
#
# Needs podman (or docker: set ENGINE=docker).

set -e

ENGINE=${ENGINE:-podman}
IMAGE=lessbrokenssh-build
cd "$(dirname "$0")"

if [[ $1 == image ]] || ! $ENGINE image exists $IMAGE 2>/dev/null; then
  echo "building $IMAGE image (first time downloads ~4GB)..."
  $ENGINE build -t $IMAGE -f Containerfile .
  [[ $1 == image ]] && exit 0
fi

if [[ ! -f opentransport-libssh2/CMakeLists.txt ]]; then
  git submodule update --init --recursive
fi

RUN=($ENGINE run --rm -v "$PWD:/src:Z" -w /src -e HOME=/tmp)
[[ -t 0 ]] && RUN+=(-it)
# keep build output owned by you rather than root
[[ $ENGINE == podman ]] && RUN+=(--userns=keep-id --user "$(id -u):$(id -g)")

if [[ $1 == shell ]]; then
  exec "${RUN[@]}" $IMAGE bash
fi

exec "${RUN[@]}" $IMAGE ./build-lessbrokenssh.bash "$@"
