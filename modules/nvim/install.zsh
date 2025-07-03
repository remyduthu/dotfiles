#!/usr/bin/env zsh

set -eu

STAGE="nvim"

source "${DOTFILES_PATH}"/src/*.zsh

require "nvim"

taskf "Link configuration files"
mkdir -p "${HOME}/.config/nvim/"
link "${DOTFILES_PATH}/modules/nvim/init.lua" "${HOME}/.config/nvim/init.lua"
link "${DOTFILES_PATH}/modules/nvim/after" "${HOME}/.config/nvim/after"
link "${DOTFILES_PATH}/modules/nvim/lua" "${HOME}/.config/nvim/lua"
