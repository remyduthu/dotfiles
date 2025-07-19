#!/usr/bin/env zsh

set -eu

STAGE="code"

source "${DOTFILES_PATH}"/src/*.zsh

require "code"

taskf "Install extensions"
for extension in \
  "alefragnani.project-manager" \
  "asvetliakov.vscode-neovim" \
  "bmewburn.vscode-intelephense-client" \
  "charliermarsh.ruff" \
  "dbaeumer.vscode-eslint" \
  "dracula-theme.theme-dracula" \
  "eamodio.gitlens" \
  "editorconfig.editorconfig" \
  "esbenp.prettier-vscode" \
  "github.copilot" \
  "github.copilot-chat" \
  "golang.go" \
  "ms-python.debugpy" \
  "ms-python.python" \
  "ms-python.vscode-pylance" \
  "ms-vsliveshare.vsliveshare" \
  "mvllow.rose-pine" \
  "redhat.vscode-xml" \
  "redhat.vscode-yaml" \
  "tamasfe.even-better-toml" \
  "timonwong.shellcheck"
do
  code --force --install-extension "${extension}" || true # Ignore errors.
done

taskf "Disable extensions"
for extension in \
  "ms-vsliveshare.vsliveshare"
do
  code --force --disable-extension "${extension}" || true # Ignore errors.
done

taskf "Link configuration files"
link "${DOTFILES_PATH}/modules/code/keybindings.json" "${HOME}/Library/Application Support/Code/User/keybindings.json"
link "${DOTFILES_PATH}/modules/code/settings.json" "${HOME}/Library/Application Support/Code/User/settings.json"
link "${DOTFILES_PATH}/modules/code/snippets.code-snippets" "${HOME}/Library/Application Support/Code/User/snippets/snippets.code-snippets"
link "${DOTFILES_PATH}/modules/code/tasks.json" "${HOME}/Library/Application Support/Code/User/tasks.json"

# https://github.com/vscode-neovim/vscode-neovim#vscode-configuration
defaults write "com.microsoft.VSCode" "ApplePressAndHoldEnabled" -boolean false
