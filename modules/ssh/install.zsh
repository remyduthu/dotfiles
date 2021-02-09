#!/usr/bin/env zsh

set -eu

STAGE="ssh"

source "${DOTFILES_PATH}"/src/*.zsh

taskf "Link configuration files"
link "${DOTFILES_PATH}/modules/ssh/config" "${HOME}/.ssh/config"

# TODO: Commit a default configuration file and ignore the actual concrete configuration
