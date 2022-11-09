#!/usr/bin/env zsh

set -eu

STAGE="iterm"

source "${DOTFILES_PATH}"/src/*.zsh

taskf "Download themes"
curl --location https://raw.githubusercontent.com/dracula/iterm/master/Dracula.itermcolors > "${DOTFILES_PATH}/modules/iterm/Dracula.itermcolors"
curl --location https://raw.githubusercontent.com/altercation/solarized/master/iterm2-colors-solarized/Solarized%20Light.itermcolors > "${DOTFILES_PATH}/modules/iterm/Solarized Light.itermcolors"
