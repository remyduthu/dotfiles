#!/usr/bin/env zsh

set -eu

STAGE="zsh"

source "${DOTFILES_PATH}"/src/*.zsh

require "kubectl" "zsh"

taskf "Install external completion files"
mkdir -p "${HOME}/.zsh/completion"
curl --location https://raw.githubusercontent.com/docker/cli/master/contrib/completion/zsh/_docker > "${HOME}/.zsh/completion/_docker"
kubectl completion zsh > "${HOME}/.zsh/completion/_kubectl"
kustomize completion zsh > "${HOME}/.zsh/completion/_kustomize"

taskf "Link configuration files"
touch "${HOME}/.hushlogin" # Remove the login banner
link "${DOTFILES_PATH}/modules/zsh/.zshrc" "${HOME}/.zshrc"
