lessbrokenssh
-------------
A hobby fork of [cy384/ssheven](https://github.com/cy384/ssheven).

The goal is to SSH from my own old Macs into an EC2 instance and run the Claude CLI without the screen breaking apart. That means getting box drawing, Unicode and color right in a modern full-screen terminal app.

Machines I want it to run on:

| Machine | CPU | Build |
|---|---|---|
| Macintosh LC II | 68030, no FPU | `68030` |
| Macintosh LC 475 | 68LC040, no FPU | `68040` |
| iMac G3 | PowerPC 750 (G3) | `g3` |

I'm also checking whether builds tuned for one CPU are actually faster than the generic `68020` and `601` builds, or whether they make no real difference.

### status

Tested against an EC2 host on the iMac G3 (Mac OS 9, 800×600, 32-bit color, `g3` build) and the LC 475 (thousands of colors, `68040` build): **the Claude CLI and btop draw correctly**, with their frames, logo, graphs, symbols and colors. The LC II hasn't been tried yet.

What works so far, compared with ssheven 0.9.0:

| | ssheven 0.9.0 | lessbrokenssh |
|---|---|---|
| Box drawing, blocks, shades, Braille, sextants, Powerline | `◊` | real glyphs (500+, 6×12) |
| Symbols (`⏺ ⎿ ✻ ❯ ✓ ☐ ↑ ⌘`…) | `◊` or `b` | hand-drawn glyphs |
| Latin-1 and Mac Roman (`é ß © ° · … • – —`) | ASCII lookalikes | the real characters |
| Emoji | `◊` | 256 color emoji (8-bit, 4-bit and dithered black-and-white versions) |
| Japanese, Korean, Chinese | `◊` | the system's own fonts, when those scripts are installed |
| Wide characters and emoji | line shifts by a column | correct widths (Unicode 16, emoji with VS16) |
| Colors | 8 colors, `TERM=xterm-16color` | 256-color and truecolor in real color on 4-bit and deeper screens, `TERM=xterm-256color` |
| Scrollback | none | 1,000 lines with a scroll bar and Shift-Page Up/Down; full-screen programs use the alternate screen |

It also fixes a bug in upstream's unreleased code, where the port typed in the connect dialog was dropped and connecting failed.

Known gaps:

- **Rare Korean syllables:** some Hangul shows `◊`, probably syllables outside the 2,350 in KS X 1001, which the classic Korean font can't reach. Under investigation.
- **Truecolor:** the app asks the server for `COLORTERM=truecolor`, but sshd only passes it on with `AcceptEnv COLORTERM`. Otherwise add `export COLORTERM=truecolor` to your shell profile on the server.
- **Copy and paste** of text outside Mac Roman.
- **800×600 font:** the iMac still uses Monaco 9 (6×12 cells). A bigger TrueType font with its own glyph set is planned.
- **Scrollback length** is fixed at 1,000 lines (`SCROLLBACK_LINES` in `ssheven-scrollback.h`); much more needs a bigger memory size in Get Info.
- **CPU builds:** not measured yet.

The design and plan are in [docs/design/](docs/design/README.md). The glyph and emoji tools are described in [tools/glyphs/README.md](tools/glyphs/README.md). Glyphs are plain text files in `glyphs/6x12/`, and emoji are PNGs in `glyphs/emoji/12x12/`, so both can be edited by hand.

### building

Needs podman (or docker, with `ENGINE=docker`). The first run builds a container with the [Retro68](https://github.com/autc04/Retro68/) toolchain and Apple's Universal Interfaces.

```
./build.sh               # all targets: 68020 68030 68040 601 g3
./build.sh 68030 g3      # just these
./build.sh shell         # shell inside the build container
./build.sh glyphs        # regenerate glyphs and previews after editing (see tools/glyphs/)
```

Each target produces `dist/ssheven-<cpu>.dsk` (HFS disk image) and `dist/ssheven-<cpu>.bin` (MacBinary). All 68k builds are soft-float, so they run on FPU-less machines like the LC II and LC 475.

Development happens on the `work` branch. `master` stays identical to upstream.

The original ssheven README follows.

---

![ssheven box](http://www.cy384.com/media/img/ssheven_box_front_small.png)

ssheven
-------
A minimal new SSH client for Mac OS 7/8/9.

Project status: as of 0.8.0 ([see github releases](https://github.com/cy384/ssheven/releases)), fairly secure and usable, but without a polished UX or all planned features.  Versions prior to 1.0.0 should be considered alpha/beta quality.

![ssheven screenshot](http://www.cy384.com/media/img/ssheven-0.8.8.png)

system requirements
-------------------
* CPU: Any PPC processor, or at least a 68030 (68040 strongly recommended).
* RAM: 2MB.
* Disk space: fits on a floppy.
* System 7.1 or later. Versions below 7.5 require the Thread Manager extension.
* Open Transport networking required, latest version possible highly recommended.

features that might happen
--------------------------
* improved unicode support
* basic scp file transfer
* configurable terminal string
* configurable/auto-choosing SSH buffer size (improves feel for faster machines)
* nicer error presentation for more failure cases
* add `known_hosts` reset option
* read Apple HIG and clean up UI/UX
* all license info in an about box type thing
* finish and upload papercraft box, floppy sticker artwork, icon/logo svg
* more complete color support
* keyboard-interactive login
* better debug output
* multiple terminal windows open at once

known problems
--------------
* drawing the screen is somewhat slow
* input latency feels high because redrawing the screen is slow (along with all the encryption, which is also slow)
* receiving a large amount of data may break the channel or cause lockups (e.g. `cat /dev/zero`)
* non-US keyboard input may or may not have issues
* [how do you pronounce ssheven?](https://github.com/cy384/ssheven/issues/8)

build
-----
Uses [Retro68](https://github.com/autc04/Retro68/) (requires the Universal headers) and cmake.

Requires mbedtls, libssh2, and libvterm, see my (cy384's) hackjobs of those libraries for details.  These are now pulled in as submodules, and everything should get built with a single CMake build.

The script `build-ssheven.bash` can be used to build a fat binary, or just as reference for build commands.

license
-------
Licensed under the BSD 2 clause license, see `LICENSE` file.

