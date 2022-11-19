#!/usr/bin/env zsh
set -eu

STAGE="rectangle"

source "${DOTFILES_PATH}"/src/*.zsh

taskf "Copy configuration file"
mkdir -p "${HOME}/Library/Application Support/Rectangle/"
cp "${DOTFILES_PATH}/modules/rectangle/RectangleConfig.json" "${HOME}/Library/Application Support/Rectangle/RectangleConfig.json"
