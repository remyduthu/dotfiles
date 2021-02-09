#!/usr/bin/env zsh

set -eu

STAGE="git"

source "${DOTFILES_PATH}"/src/*.zsh

require "git"

taskf "Link configuration files"
link "${DOTFILES_PATH}/modules/git/.gitconfig" "${HOME}/.gitconfig"
link "${DOTFILES_PATH}/modules/git/.gitignore" "${HOME}/.gitignore"
