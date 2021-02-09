#!/usr/bin/env zsh

set -eu

export DOTFILES_PATH="${PWD}"

source "${DOTFILES_PATH}"/src/*.zsh

for script in "${DOTFILES_PATH}"/modules/(brew|code|git|iterm|nvim|ssh|system|zsh)/install.zsh
do
  [[ -f "${script}" ]] && "${script}"
done
