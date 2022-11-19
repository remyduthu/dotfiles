#!/usr/bin/env zsh

set -eu

export DOTFILES_PATH="${PWD}"

source "${DOTFILES_PATH}"/src/*.zsh

STAGE="export"

DESTINATION="${1}"
if [[ -f "${DESTINATION}" ]] {
  errorf "${DESTINATION} does not exist"
}

function export_directory() {
  taskf "Back up ${1}"
  rsync --human-readable --recursive --stats "${HOME}/${1}" "${DESTINATION}"
}

export_directory ".kube"
export_directory ".ssh"
export_directory "Pictures"
