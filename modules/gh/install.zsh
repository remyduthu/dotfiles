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
link "${DOTFILES_PATH}/modules/gh/bin/gh-reviews-dashboard" "${HOME}/.local/bin/gh-reviews-dashboard"

taskf "Install reviews dashboard launchd agent"
PLIST_SRC="${DOTFILES_PATH}/modules/gh/com.github.reviews-dashboard.plist"
PLIST_DST="${HOME}/Library/LaunchAgents/com.github.reviews-dashboard.plist"
mkdir -p "${HOME}/Library/LaunchAgents"
link "${PLIST_SRC}" "${PLIST_DST}"
launchctl bootout "gui/$(id -u)" "${PLIST_DST}" 2>/dev/null || true
launchctl bootstrap "gui/$(id -u)" "${PLIST_DST}"
