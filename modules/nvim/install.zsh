#!/usr/bin/env zsh

set -eu

STAGE="nvim"

source "${DOTFILES_PATH}"/src/*.zsh

require "nvim"

taskf "Link configuration files"
mkdir -p "${HOME}/.config/nvim/"
link "${DOTFILES_PATH}/modules/nvim/init.vim" "${HOME}/.config/nvim/init.vim"
