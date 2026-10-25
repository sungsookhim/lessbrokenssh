lessbrokenssh
-------------
I made this fork with Claude ([Claude Code](https://claude.com/claude-code)) so I could work on my projects from the old Macs I have at hand.

A hobby fork of [cy384/ssheven](https://github.com/cy384/ssheven), renamed so the two can live side by side: the app, its source files and its builds are called lessbrokenssh, and it keeps its own preferences and known-hosts files (`lessbrokenssh Preferences`, `lessbrokenssh known_hosts`) and creator code (`LBSH`). It's still under ssheven's BSD 2-clause license, with cy384's copyright; see `LICENSE`.

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
| Emoji | `◊` | only a selected 256 of Unicode's emoji, in color (8-bit, 4-bit and dithered black-and-white versions); the rest still show as `◊` |
| Japanese, Korean, Chinese | `◊` | the system's own fonts, when those scripts are installed |
| Wide characters and emoji | line shifts by a column | correct widths (Unicode 16, emoji with VS16) |
| Colors | 8 colors, `TERM=xterm-16color` | 256-color and truecolor in real color on 4-bit and deeper screens, `TERM=xterm-256color` |
| Scrollback | none | 1,000 lines with a scroll bar and Shift-Page Up/Down; full-screen programs use the alternate screen |
| Keys and mouse | Shift-Tab sends Tab; clicks only reach programs in the basic mouse mode | Shift-Tab sends back-tab; clicks reach programs in any mouse mode (Shift-click selects text) |
| Responsiveness | redraws the whole screen several times a second and sleeps ~130 ms between looks at the network | redraws only changed rows, and checks for incoming data every tick while connected |

It also fixes a bug in upstream's unreleased code, where the port typed in the connect dialog was dropped and connecting failed.

Keys worth knowing:

| Keys | Does |
|---|---|
| Shift-Page Up / Shift-Page Down, or the scroll bar | scroll lessbrokenssh's history |
| Page Up / Page Down | go to the program |
| Option-Return | Meta-Return; a new line in the Claude CLI's input instead of sending |
| Shift-Tab | back-tab; cycles the Claude CLI's modes |
| Esc | Escape; interrupts the Claude CLI |
| Shift-click | selects text even when the program uses the mouse |

In the Claude CLI, Ctrl-O opens its own view for reading back through the output.

Known gaps:

- **CJK needs the system's language kits.** Korean and Japanese draw with the Mac's own fonts, so a Mac without them (like an English System 7.6) shows `◊`. Hangul syllables outside the 2,350 in KS X 1001 also show `◊`, even with the Korean kit.
- **Old Korean text files** are usually EUC-KR, not UTF-8, so `cat` shows `◊`. Convert them on the server: `iconv -f cp949 -t utf-8 file`.
- **Truecolor:** the app asks the server for `COLORTERM=truecolor`, but sshd only passes it on with `AcceptEnv COLORTERM`. Otherwise add `export COLORTERM=truecolor` to your shell profile on the server.
- **Scrollback** is 1,000 lines (`SCROLLBACK_LINES` in `lessbrokenssh-scrollback.h`); much more needs a bigger memory size in Get Info.
- **btop is slow on the LC 475.** Its refreshes carry tens of KB of color codes, and decrypting and parsing those keeps a 25 MHz 68LC040 busy. It helps to set `update_ms` to 4000 or more, `truecolor = False` and a flat theme like `TTY` in btop's options. top and htop run fine.

To do, or ideas to keep in mind:

- **Bundled CJK bitmaps** for Macs without the Korean or Japanese language kits (like an English System 7.6), and for the rare Hangul syllables outside KS X 1001. All 11,172 syllables plus kana and common kanji, exported like the emoji, would be about 250–400 KB. The catch: with 6×12 cells a CJK character only gets 12×12 px, which is the bare minimum. Complex Hangul (`읽 많 됐`) and dense kanji lose strokes, so this would be more worthwhile together with larger cells.
- **Larger cells on 800×600** (8×16, so 16×16 for CJK): a TrueType base font and an 8×16 glyph and emoji set.
- **Unicode copy and paste**, and typing in Korean or Japanese: text currently leaves the Mac as Mac Roman (or the script's own encoding), not UTF-8.
- **Scrollback length** as a preference instead of a constant.
- **Faster drawing on 68k:** draw each row's glyphs with one copy instead of one per cell, which matters most for btop's Braille graphs.
- **Mouse dragging** for programs that track it (only press and release are sent now).
- **Measure the CPU-tuned builds** against the generic `68020` and `601` ones.
- **Ed25519 keys**, which this libssh2 build has turned off (RSA and ECDSA keys work).
- **Tag a release** with the `.bin` files. The two upstream bugs fixed here (the dropped port, `88a7ad8`, and `TERM` not being set, `8fe357b`) can go to cy384/ssheven if they're ever wanted.

The design and plan are in [docs/design/](docs/design/README.md). The glyph and emoji tools are described in [tools/glyphs/README.md](tools/glyphs/README.md). The app icon and About picture are PNGs in `docs/lessbrokenssh-icons/`, turned into `lessbrokenssh-icons.r` by `tools/icons/make_icons.py` on every build. Glyphs are plain text files in `glyphs/6x12/`, and emoji are PNGs in `glyphs/emoji/12x12/`, so both can be edited by hand.

### building

Needs podman (or docker, with `ENGINE=docker`). The first run builds a container with the [Retro68](https://github.com/autc04/Retro68/) toolchain and Apple's Universal Interfaces.

```
./build.sh               # all targets: 68020 68030 68040 601 g3
./build.sh 68030 g3      # just these
./build.sh shell         # shell inside the build container
./build.sh glyphs        # regenerate glyphs and previews after editing (see tools/glyphs/)
```

Each target produces `dist/lessbrokenssh-<cpu>.dsk` (HFS disk image) and `dist/lessbrokenssh-<cpu>.bin` (MacBinary). All 68k builds are soft-float, so they run on FPU-less machines like the LC II and LC 475.

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

