#!/usr/bin/env zsh

set -eu

STAGE="pipx"

source "${DOTFILES_PATH}"/src/*.zsh

require "pipx"

taskf "Install packages"
packages=(
  mergify-cli
  poethepoet
  poetry
  pytest
  reno
  ruff
)
pipx upgrade --install "${packages[@]}"
