lessbrokenssh @VERSION@
=================

An SSH client for Mac OS 7, 8 and 9, forked from ssheven by cy384.
It draws box drawing, symbols, emoji, colors and CJK text from modern
full-screen terminal programs.

Which app to use
----------------

lessbrokenssh 68020    any 68k Mac with a 68020 or 68030
                       (Mac II family, LC, LC II, LC III, IIci, SE/30)
lessbrokenssh 68040    68040 Macs (Quadra, Centris, LC 475, LC 575)
lessbrokenssh PowerPC  any PowerPC Mac (601, 603, 604, G3, G4)

The 68020 app also runs on a 68040, just tuned less well. Only one of
the three is needed; the others can be thrown away.

Requirements
------------

- System 7.1 or later (below 7.5, the Thread Manager extension)
- Open Transport
- 4 MB of free memory (3 MB minimum)
- No FPU needed

Settings are kept in "lessbrokenssh Preferences" and
"lessbrokenssh known_hosts" in the Preferences folder, apart from
ssheven's, so both apps can be used side by side.

More: https://github.com/sungsookhim/lessbrokenssh
License: BSD 2-clause, Copyright cy384 (see the LICENSE file on GitHub)
Ed25519 and curve25519: Monocypher (monocypher.org), CC0 or BSD 2-clause
