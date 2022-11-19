#!/usr/bin/env zsh
set -eu

STAGE="krew"

source "${DOTFILES_PATH}"/src/*.zsh

require "kubectl"

taskf "Install dependencies"
kubectl krew install \
  "lineage" \
  "resource-capacity" \
  "score"
