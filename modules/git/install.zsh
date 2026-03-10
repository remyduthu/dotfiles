#!/usr/bin/env zsh

set -eu

STAGE="git"

source "${DOTFILES_PATH}"/src/*.zsh

require "git"

taskf "Link configuration files"
link "${DOTFILES_PATH}/modules/git/.gitconfig" "${HOME}/.gitconfig"
link "${DOTFILES_PATH}/modules/git/.gitignore" "${HOME}/.gitignore"

taskf "Link custom Git commands"
mkdir -p "${HOME}/.local/bin"
link "${DOTFILES_PATH}/modules/git/bin/git-cleanup" "${HOME}/.local/bin/git-cleanup"
link "${DOTFILES_PATH}/modules/git/bin/git-worktree-init" "${HOME}/.local/bin/git-worktree-init"
