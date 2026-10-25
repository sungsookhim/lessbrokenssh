#!/bin/bash
set -e

# usage: build-lessbrokenssh.bash [target...]
#
# targets:
#   68020 68040         68k builds tuned for that CPU (both soft-float); the
#                       68020 one also covers the 68030, which compiles the same
#   g3                  PowerPC build tuned for the 750 (G3); runs on any PowerPC
#   601                 PowerPC build tuned for the 601, for comparing speed
#   all                 68020 68040 g3 (the default)
#   release             all, then the release files in dist/release/ (see
#                       make_release below)
#   glyphs              regenerate procedural glyphs (keeping hand-edited ones),
#                       pack them, and render previews into build-glyphs/
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

# glyphs/ -> glyphs.r, so hand edits to glyphs are always in the build
if command -v python3 >/dev/null; then
  python3 tools/glyphs/pack.py
fi

# docs/lessbrokenssh-icons/*.png -> lessbrokenssh-icons.r
if python3 -c 'import PIL' 2>/dev/null; then
  python3 tools/icons/make_icons.py
fi

# build_cpu <target> <toolchain file> <gcc -mcpu value>
build_cpu() {
  echo "building $1..."
  cmake -S . -B build-$1 -DCMAKE_TOOLCHAIN_FILE=$2 -DSSHEVEN_CPU=$3
  cmake --build build-$1 $BUILD_PARALLEL
  cp build-$1/lessbrokenssh.dsk dist/lessbrokenssh-$1.dsk
  cp build-$1/lessbrokenssh.bin dist/lessbrokenssh-$1.bin
}

# make_release: dist/release/lessbrokenssh-<version>-<cpu>.bin for each release
# build, and one lessbrokenssh-<version>.dsk holding all three apps and a Read Me
make_release() {
  local version=$(sed -n 's/^#define SSHEVEN_VERSION *"\(.*\)"/\1/p' lessbrokenssh-constants.r)
  local out=dist/release
  local dsk=$out/lessbrokenssh-$version.dsk
  rm -rf $out && mkdir -p $out
  for cpu in 68020 68040 g3; do
    cp dist/lessbrokenssh-$cpu.bin $out/lessbrokenssh-$version-$cpu.bin
  done

  # sized to fit: the apps plus 25% and 256 KB for HFS overhead
  local kb=$(( $(cat $out/*.bin | wc -c) * 5 / 4 / 1024 + 256 ))
  dd if=/dev/zero of=$dsk bs=1024 count=$kb status=none
  hformat -l "lessbrokenssh $version" $dsk >/dev/null
  hmount $dsk >/dev/null
  hcopy -m $out/lessbrokenssh-$version-68020.bin ":lessbrokenssh 68020"
  hcopy -m $out/lessbrokenssh-$version-68040.bin ":lessbrokenssh 68040"
  hcopy -m $out/lessbrokenssh-$version-g3.bin ":lessbrokenssh PowerPC"
  sed "s/@VERSION@/$version/g" docs/releases/readme.txt > $out/readme.tmp
  hcopy -t $out/readme.tmp ":Read Me"
  hattrib -t TEXT -c ttxt ":Read Me"
  hls -l
  humount >/dev/null
  rm $out/readme.tmp
  echo "release files in $out/"
}

TARGETS=("$@")
[[ ${#TARGETS[@]} -eq 0 ]] && TARGETS=(all)

for target in "${TARGETS[@]}"; do
  case $target in
    68020|68040)       build_cpu $target $TOOLCHAIN_68K $target ;;
    601)               build_cpu 601 $TOOLCHAIN_PPC 601 ;;
    g3)                build_cpu g3 $TOOLCHAIN_PPC 750 ;;
    glyphs)
      python3 tools/glyphs/procedural.py
      python3 tools/glyphs/export_font.py
      python3 tools/glyphs/pack.py
      python3 tools/glyphs/preview.py
      ;;
    all|release)
      for cpu in 68020 68040; do build_cpu $cpu $TOOLCHAIN_68K $cpu; done
      build_cpu g3 $TOOLCHAIN_PPC 750
      [[ $target == release ]] && make_release
      ;;
    *) echo "unknown target: $target (try 68020 68040 g3 601 all release glyphs)"; exit 1 ;;
  esac
done

echo "done; results in dist/"
