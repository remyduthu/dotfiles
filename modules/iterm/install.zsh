#!/usr/bin/env zsh

set -eu

STAGE="iterm"

source "${DOTFILES_PATH}"/src/*.zsh

taskf "Download themes"
curl --location https://raw.githubusercontent.com/altercation/solarized/master/iterm2-colors-solarized/Solarized%20Light.itermcolors > "${DOTFILES_PATH}/modules/iterm/Solarized Light.itermcolors"

taskf "Load configuration file"
defaults write "com.googlecode.iterm2" "LoadPrefsFromCustomFolder" -boolean true
defaults write "com.googlecode.iterm2" "PrefsCustomFolder" -string "${DOTFILES_PATH}/modules/iterm/"

# Update the configuration file when quitting the application.
defaults write "com.googlecode.iterm2" "NoSyncNeverRemindPrefsChangesLostForFile" -boolean true
defaults write "com.googlecode.iterm2" "NoSyncNeverRemindPrefsChangesLostForFile_selection" -integer 0

