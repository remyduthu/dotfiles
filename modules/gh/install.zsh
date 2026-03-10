#!/usr/bin/env zsh

set -eu

STAGE="gh"

source "${DOTFILES_PATH}"/src/*.zsh

require "gh"

taskf "Link configuration files"
link "${DOTFILES_PATH}/modules/gh/config.yml" "${HOME}/.config/gh/config.yml"
