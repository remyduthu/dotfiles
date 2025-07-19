#!/usr/bin/env zsh

set -eu

export DOTFILES_PATH="${PWD}"

source "${DOTFILES_PATH}"/src/*.zsh

STAGE="init"

xcode-select --print-path &> /dev/null
if [[ ${?} != 0 ]] {
  taskf "Install Xcode Command Line Tools"
  xcode-select --install
}

require "brew" &> /dev/null
if [[ ${?} != 0 ]] {
  taskf "Install Homebrew"
  /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
}

unset STAGE

function install_modules() {
  for module in "${@}"
  do
    install_script="${DOTFILES_PATH}/modules/${module}/install.zsh"

    if [[ -f "${install_script}" ]] {
      "${install_script}"
    }
  done
}

if [[ -n ${@} ]] {
  install_modules "${@}"
} else {
  # Without arguments, install all modules.
  install_modules "brew" "code" "git" "go" "iterm" "krew" "nvim" "pipx" "ssh" "system" "zsh"
}


