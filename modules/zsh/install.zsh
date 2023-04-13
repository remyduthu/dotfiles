#!/usr/bin/env zsh

set -eu

STAGE="zsh"

source "${DOTFILES_PATH}"/src/*.zsh

function as_sudo() {
  sudo bash -c "${@}"
}

require "kubectl" "zsh"

taskf "Install external completion files"
FPATH=/usr/local/share/zsh/site-functions/
as_sudo "mkdir -p ${FPATH}"
as_sudo "curl --location https://raw.githubusercontent.com/docker/cli/master/contrib/completion/zsh/_docker > ${FPATH}/_docker"
as_sudo "kubectl completion zsh > ${FPATH}/_kubectl"
as_sudo "kustomize completion zsh > ${FPATH}/_kustomize"

taskf "Link configuration files"
touch "${HOME}/.hushlogin" # Remove the login banner
link "${DOTFILES_PATH}/modules/zsh/.zshrc" "${HOME}/.zshrc"
