#!/usr/bin/env zsh

set -eu

STAGE="claude"

source "${DOTFILES_PATH}"/src/*.zsh

require "claude"

taskf "Link configuration files"
link "${DOTFILES_PATH}/modules/claude/settings.json" "${HOME}/.claude/settings.json"
link "${DOTFILES_PATH}/modules/claude/CLAUDE.md" "${HOME}/.claude/CLAUDE.md"

taskf "Link commands"
link "${DOTFILES_PATH}/modules/claude/commands/babysit-mergify-ci.md" "${HOME}/.claude/commands/babysit-mergify-ci.md"
link "${DOTFILES_PATH}/modules/claude/commands/watch-mergify-engine-deployment.md" "${HOME}/.claude/commands/watch-mergify-engine-deployment.md"
