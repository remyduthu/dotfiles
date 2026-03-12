#!/usr/bin/env zsh

set -eu

STAGE="gh"

source "${DOTFILES_PATH}"/src/*.zsh

require "gh"

taskf "Link configuration files"
link "${DOTFILES_PATH}/modules/gh/config.yml" "${HOME}/.config/gh/config.yml"

taskf "Link scripts"
link "${DOTFILES_PATH}/modules/gh/bin/gh-daily" "${HOME}/.local/bin/gh-daily"
link "${DOTFILES_PATH}/modules/gh/bin/gh-reviews" "${HOME}/.local/bin/gh-reviews"
