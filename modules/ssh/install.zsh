#!/usr/bin/env zsh

set -eu

STAGE="ssh"

source "${DOTFILES_PATH}"/src/*.zsh

taskf "Link configuration files"
mkdir -p ~/.ssh/sockets/
link "${DOTFILES_PATH}/modules/ssh/config" "${HOME}/.ssh/config"
sudo cp "${DOTFILES_PATH}/modules/ssh/hosts" "/etc/hosts"
