#!/usr/bin/env zsh

set -eu

STAGE="brew"

source "${DOTFILES_PATH}"/src/*.zsh

require "brew"

taskf "Install dependencies"
brew update
brew bundle install --file="${DOTFILES_PATH}/modules/brew/Brewfile" --no-lock

taskf "Reset the LaunchPad"
osascript -e 'tell application "System Preferences" to quit'
defaults write com.apple.dock ResetLaunchPad -bool true
killall Dock
