#!/usr/bin/env zsh

set -eu

STAGE="npm"

source "${DOTFILES_PATH}"/src/*.zsh

require "npm"

taskf "Install global packages"
packages=(
  @anthropic-ai/claude-code
)
npm install --global "${packages[@]}"
