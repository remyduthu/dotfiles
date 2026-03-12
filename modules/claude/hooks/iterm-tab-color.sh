#!/usr/bin/env bash
# Set iTerm2 tab color based on Claude Code state.

set -eu

set_tab_color() {
  printf "\033]6;1;bg;red;brightness;%d\007" "$1" > /dev/tty
  printf "\033]6;1;bg;green;brightness;%d\007" "$2" > /dev/tty
  printf "\033]6;1;bg;blue;brightness;%d\007" "$3" > /dev/tty
}

reset_tab_color() {
  printf "\033]6;1;bg;*;default\007" > /dev/tty
}

case "${1:-}" in
  working)  set_tab_color 110 160 220 ;;
  waiting)  set_tab_color 225 175 95 ;;
  reset)    reset_tab_color ;;
  *)        echo "Usage: $0 {working|waiting|reset}" >&2; exit 1 ;;
esac
