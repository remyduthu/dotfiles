#!/usr/bin/env zsh

set -eu

STAGE="system"

source "${DOTFILES_PATH}"/src/*.zsh

taskf "Apply system defaults"

osascript -e 'tell application "System Preferences" to quit'

set -x # Show commands

# Keyboard
defaults write "Apple Global Domain" "InitialKeyRepeat" -int 25
defaults write "Apple Global Domain" "KeyRepeat" -int 5

# Screen
defaults write -g CGFontRenderingFontSmoothingDisabled -bool false

# Dock
defaults write "com.apple.dock" "autohide-delay" -float 0
defaults write "com.apple.dock" "autohide-time-modifier" -float 0
defaults write "com.apple.dock" "autohide" -boolean true
defaults write "com.apple.dock" "persistent-apps" -array
defaults write "com.apple.dock" "show-recents" -bool false
defaults write "com.apple.dock" "tilesize" -integer 32

# Finder
defaults write "Apple Global Domain" "AppleShowAllExtensions" -bool true
defaults write "com.apple.finder" "FXDefaultSearchScope" -string "SCcf" # Search the current folder by default
defaults write "com.apple.finder" "FXPreferredViewStyle" -string "Nlsv" # Use the list view by default
defaults write "com.apple.finder" "ShowPathbar" -bool true
defaults write "com.apple.finder" "ShowStatusBar" -bool true

# Security (https://www.bejarano.io/hardening-macos/)
defaults write "Apple Global Domain" "AppleShowAllExtensions" -boolean true
defaults write "com.apple.AdLib" "allowApplePersonalizedAdvertising" -boolean false
defaults write "com.apple.Safari" "AutoOpenSafeDownloads" -boolean false
defaults write "com.apple.Terminal" "SecureKeyboardEntry" -boolean true
defaults write "com.googlecode.iterm2" "Secure Input" -boolean true

set +x

for app in "Dock" "Finder" "Safari" "SystemUIServer"
do
  killall "${app}" || true
done

taskf "Link configuration files"
sudo cp "${DOTFILES_PATH}/modules/system/hosts" "/etc/hosts" || true
