#!/bin/bash
set -e

# usage: build-ssheven.bash [target...]
#
# targets:
#   68020 68030 68040   68k builds tuned for that CPU (all soft-float)
#   601 g3              PowerPC builds tuned for the 601 or the 750 (G3)
#   all                 everything above (the default)
#
# Each target builds in build-<target>/ and copies its .dsk (HFS disk image)
# and .bin (MacBinary) into dist/.

# set RETRO68_PATH to the root of your Retro68 build folder, e.g. ~/src/Retro68-build/
# (the build container from ./build.sh sets it for you)
if [[ -z $RETRO68_PATH ]]; then
  echo "Set RETRO68_PATH to your Retro68 build folder, or use ./build.sh"
  exit 1
fi

# check for nproc to count processors to build parallel
BUILD_PARALLEL=
if command -v nproc 2>&1 >/dev/null
then
  BUILD_PARALLEL="--parallel $(nproc)"
fi

TOOLCHAIN_68K=$RETRO68_PATH/toolchain/m68k-apple-macos/cmake/retro68.toolchain.cmake
TOOLCHAIN_PPC=$RETRO68_PATH/toolchain/powerpc-apple-macos/cmake/retroppc.toolchain.cmake

mkdir -p dist

# build_cpu <target> <toolchain file> <gcc -mcpu value>
build_cpu() {
  echo "building $1..."
  cmake -S . -B build-$1 -DCMAKE_TOOLCHAIN_FILE=$2 -DSSHEVEN_CPU=$3
  cmake --build build-$1 $BUILD_PARALLEL
  cp build-$1/ssheven.dsk dist/ssheven-$1.dsk
  cp build-$1/ssheven.bin dist/ssheven-$1.bin
}

TARGETS=("$@")
[[ ${#TARGETS[@]} -eq 0 ]] && TARGETS=(all)

for target in "${TARGETS[@]}"; do
  case $target in
    68020|68030|68040) build_cpu $target $TOOLCHAIN_68K $target ;;
    601)               build_cpu 601 $TOOLCHAIN_PPC 601 ;;
    g3)                build_cpu g3 $TOOLCHAIN_PPC 750 ;;
    all)
      for cpu in 68020 68030 68040; do build_cpu $cpu $TOOLCHAIN_68K $cpu; done
      build_cpu 601 $TOOLCHAIN_PPC 601
      build_cpu g3 $TOOLCHAIN_PPC 750
      ;;
    *) echo "unknown target: $target (try 68020 68030 68040 601 g3 all)"; exit 1 ;;
  esac
done

echo "done; results in dist/"
