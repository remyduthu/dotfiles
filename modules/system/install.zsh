#!/usr/bin/env zsh

set -eu

STAGE="system"

source "${DOTFILES_PATH}"/src/*.zsh

taskf "Apply the configuration"

osascript -e 'tell application "System Preferences" to quit'

# Keyboard
#

defaults write NSGlobalDomain NSAutomaticCapitalizationEnabled -bool false
defaults write NSGlobalDomain NSAutomaticDashSubstitutionEnabled -bool false
defaults write NSGlobalDomain NSAutomaticPeriodSubstitutionEnabled -bool false
defaults write NSGlobalDomain NSAutomaticQuoteSubstitutionEnabled -bool false
defaults write NSGlobalDomain NSAutomaticSpellingCorrectionEnabled -bool false

defaults write NSGlobalDomain KeyRepeat -int 2
defaults write NSGlobalDomain InitialKeyRepeat -int 15

# Enable full keyboard access for all controls (e.g. enable Tab in modal
# dialogs)
defaults write NSGlobalDomain AppleKeyboardUIMode -int 3

defaults write NSGlobalDomain AppleLanguages -array "en-FR" "fr-FR"
defaults write NSGlobalDomain AppleLocale -string "en_FR"
defaults write NSGlobalDomain AppleMeasurementUnits -string "Centimeters"
defaults write NSGlobalDomain AppleMetricUnits -bool true

sudo systemsetup -settimezone "Europe/Paris" &> /dev/null

# Trackpad
#

# Enable "tap to click"
defaults write com.apple.driver.AppleBluetoothMultitouch.trackpad Clicking -bool true
defaults -currentHost write NSGlobalDomain com.apple.mouse.tapBehavior -int 1
defaults write NSGlobalDomain com.apple.mouse.tapBehavior -int 1

# Enhance the Bluetooth sound quality
defaults write com.apple.BluetoothAudioAgent "Apple Bitpool Min (editable)" -int 40

# Screen
#

sudo systemsetup -setsleep 1 &> /dev/null

defaults write com.apple.screensaver askForPassword -int 1
defaults write com.apple.screensaver askForPasswordDelay -int 0

# https://github.com/kevinSuttle/macOS-Defaults/issues/17#issuecomment-266633501
defaults write NSGlobalDomain AppleFontSmoothing -int 1

# Finder
#

defaults write NSGlobalDomain AppleShowAllExtensions -bool true

defaults write com.apple.finder ShowStatusBar -bool true
defaults write com.apple.finder ShowPathbar -bool true

# Search the current folder by default
defaults write com.apple.finder FXDefaultSearchScope -string "SCcf"

# Use the list view by default
defaults write com.apple.finder FXPreferredViewStyle -string "Nlsv"

# Dock
#

# Empty the persistent applications
defaults write com.apple.dock persistent-apps -array
defaults write com.apple.dock show-recents -bool false

# Don’t rearrange the spaces
defaults write com.apple.dock mru-spaces -bool false

defaults write com.apple.dock autohide -bool true
defaults write com.apple.dock autohide-delay -float 0
defaults write com.apple.dock autohide-time-modifier -float 0
defaults write com.apple.dock launchanim -bool false
defaults write com.apple.dock tilesize -int 36

# Safari
#

defaults write com.apple.Safari HomePage -string "about:blank"
defaults write com.apple.Safari ShowFullURLInSmartSearchField -bool true

for app in "Dock" "Finder" "Safari" "SystemUIServer"
do
  killall "${app}" &> /dev/null
done
