#!/usr/bin/env zsh

set -eu

STAGE="go"

source "${DOTFILES_PATH}"/src/*.zsh

require "go"

taskf "Install dependencies"
go install github.com/catilac/plistwatch@latest
