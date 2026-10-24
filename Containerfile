# lessbrokenssh build environment
#
# Retro68 cross toolchain (m68k + PowerPC) with Apple's Universal Interfaces
# installed, which ssheven needs for Open Transport and the Thread Manager.
#
# Build the image with ./build.sh (or: podman build -t lessbrokenssh-build .)

FROM ghcr.io/autc04/retro68:latest

# MPW Golden Master disk image; contains Interfaces&Libraries (Universal Interfaces 3.4)
ARG INTERFACESFILE=https://web.archive.org/web/2019/http://staticky.com/mirrors/ftp.apple.com/developer/Tool_Chest/Core_Mac_OS_Tools/MPW_etc./MPW-GM_Images/MPW-GM.img.bin

# the entrypoint downloads, extracts, and links the universal interfaces when
# INTERFACES=universal; run it once here so the result is baked into the image
ENV INTERFACES=universal
# (fetched here because the entrypoint's curl doesn't follow archive.org redirects)
RUN curl -fsSL "$INTERFACESFILE" -o /MPW-GM.img.bin \
    && INTERFACESFILE=/MPW-GM.img.bin /Retro68-build/bin/docker-entrypoint.sh true \
    && rm -rf /tmp/* /MPW-GM.img.bin

# links are now in place; stop the entrypoint relinking on every run, which
# would fail anyway when the container runs as a non-root user
ENV INTERFACES=

# for the glyph tools in tools/glyphs
# (fonts: symbol sources for tools/glyphs/export_font.py, DejaVu and Noto are freely licensed)
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends python3-pil python3-fonttools \
        fonts-dejavu-core fonts-noto-core \
    && rm -rf /var/lib/apt/lists/*

# color emoji for tools/glyphs/export_emoji.py: the Unicode 16 release, to match
# the width table in our libvterm (Ubuntu's own copy stops at Unicode 14)
ARG NOTO_EMOJI=https://github.com/googlefonts/noto-emoji/raw/v2.048/fonts/NotoColorEmoji.ttf
RUN curl -fsSL "$NOTO_EMOJI" -o /usr/local/share/fonts/NotoColorEmoji.ttf

ENV RETRO68_PATH=/Retro68-build
WORKDIR /src
