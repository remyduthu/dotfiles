#!/usr/bin/env zsh

set -eu

STAGE="claude"

source "${DOTFILES_PATH}"/src/*.zsh

require "claude"

taskf "Link configuration files"
link "${DOTFILES_PATH}/modules/claude/settings.json" "${HOME}/.claude/settings.json"
link "${DOTFILES_PATH}/modules/claude/CLAUDE.md" "${HOME}/.claude/CLAUDE.md"

taskf "Link skills"
link "${DOTFILES_PATH}/modules/claude/skills/ship-issue" "${HOME}/.claude/skills/ship-issue"
link "${DOTFILES_PATH}/modules/claude/skills/ship-issues" "${HOME}/.claude/skills/ship-issues"
link "${DOTFILES_PATH}/modules/claude/skills/ship-idea" "${HOME}/.claude/skills/ship-idea"
link "${DOTFILES_PATH}/modules/claude/skills/say" "${HOME}/.claude/skills/say"
link "${DOTFILES_PATH}/modules/claude/skills/close-session" "${HOME}/.claude/skills/close-session"
