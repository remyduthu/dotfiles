#!/usr/bin/env zsh

set -eu

STAGE="code"

source "${DOTFILES_PATH}"/src/*.zsh

require "code"

taskf "Link configuration files"
link "${DOTFILES_PATH}/modules/code/settings.json" "${HOME}/Library/Application Support/Code/User/settings.json"
