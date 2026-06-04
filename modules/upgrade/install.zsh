#!/usr/bin/env zsh

set -eu

STAGE="upgrade"

source "${DOTFILES_PATH}"/src/*.zsh

require "brew" "pipx"

label="local.dotfiles.upgrade"
agents_dir="${HOME}/Library/LaunchAgents"
plist="${agents_dir}/${label}.plist"

taskf "Link upgrade script"
mkdir -p "${HOME}/.local/bin"
link "${DOTFILES_PATH}/modules/upgrade/upgrade.zsh" "${HOME}/.local/bin/dotfiles-upgrade"

taskf "Install launchd agent"
mkdir -p "${agents_dir}"
# launchd does not expand '$HOME' inside plist strings, so we render absolute paths.
sed "s|__HOME__|${HOME}|g" \
  "${DOTFILES_PATH}/modules/upgrade/${label}.plist" > "${plist}"

taskf "Reload launchd agent"
launchctl bootout "gui/$(id -u)/${label}" 2> /dev/null || true
launchctl bootstrap "gui/$(id -u)" "${plist}"
