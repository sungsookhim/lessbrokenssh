#!/bin/sh
# Color test for lessbrokenssh: run it on the server (sh colors.sh).
# Each section should look smooth and distinct on a 4-bit or deeper screen.

echo "TERM=$TERM, tput colors: $(tput colors 2>/dev/null)"

echo
echo "16 colors (normal, then bright):"
for c in 0 1 2 3 4 5 6 7; do printf '\033[4%sm  \033[0m' $c; done; echo
for c in 0 1 2 3 4 5 6 7; do printf '\033[10%sm  \033[0m' $c; done; echo
for c in 0 1 2 3 4 5 6 7; do printf '\033[3%sm#%s\033[0m' $c $c; done
for c in 0 1 2 3 4 5 6 7; do printf '\033[9%sm#%s\033[0m' $c $c; done; echo

echo
echo "256 colors: 6x6x6 cube, then the grey ramp:"
for row in 0 1 2 3 4 5; do
  for col in $(seq 0 35); do
    c=$((16 + row * 36 + col))
    printf '\033[48;5;%sm \033[0m' $c
  done
  echo
done
for c in $(seq 232 255); do printf '\033[48;5;%sm  \033[0m' $c; done; echo

echo
echo "truecolor: red, green, blue and grey ramps:"
for ch in r g b w; do
  for i in $(seq 0 63); do
    v=$((i * 4))
    case $ch in
      r) rgb="$v;0;0" ;; g) rgb="0;$v;0" ;; b) rgb="0;0;$v" ;; w) rgb="$v;$v;$v" ;;
    esac
    printf '\033[48;2;%sm \033[0m' "$rgb"
  done
  echo
done

echo
echo "Claude CLI-ish: \033[38;2;215;119;87m● orange\033[0m \033[38;2;153;153;153mgrey secondary text\033[0m \033[38;2;78;186;101m✓ green\033[0m \033[38;2;255;107;128m✗ pink\033[0m"
