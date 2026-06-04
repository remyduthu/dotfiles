#!/usr/bin/env zsh

# Unattended upgrade routine run by the launchd agent (see install.zsh).
# Standalone by design: launchd provides a minimal environment, so we load the
# Homebrew environment ourselves and avoid the repo's src helpers.

# Load Homebrew (Apple Silicon first, Intel fallback).
if [[ -x /opt/homebrew/bin/brew ]] {
  eval "$(/opt/homebrew/bin/brew shellenv)"
} elif [[ -x /usr/local/bin/brew ]] {
  eval "$(/usr/local/bin/brew shellenv)"
}

export HOMEBREW_NO_ENV_HINTS=1

function log() {
  echo "$(date '+%Y-%m-%dT%H:%M:%S') ${@}"
}

# Run a step, logging failures without aborting the routine.
function step() {
  log "=> ${@}"
  "${@}" || log "!! failed: ${@}"
}

log "=== dotfiles upgrade start ==="
step brew update
step brew upgrade          # Formulae and casks.
step brew cleanup
command -v pipx > /dev/null && step pipx upgrade-all
log "=== dotfiles upgrade end ==="
