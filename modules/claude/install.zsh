#!/usr/bin/env zsh

set -eu

STAGE="claude"

source "${DOTFILES_PATH}"/src/*.zsh

require "claude"

taskf "Link configuration files"
link "${DOTFILES_PATH}/modules/claude/settings.json" "${HOME}/.claude/settings.json"
link "${DOTFILES_PATH}/modules/claude/CLAUDE.md" "${HOME}/.claude/CLAUDE.md"
