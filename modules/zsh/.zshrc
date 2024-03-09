# `.zshrc` is sourced in interactive shells
# (https://zsh.sourceforge.io/Contrib/startup/)

# ZSH options: http://zsh.sourceforge.net/Doc/Release/Options.html

# The following `autoload` options are mainly used to avoid conflicts with
# existing commands and functions (`man zshbuiltins`)
#
# -U    Ignore aliases
# -z    Use Zsh style
autoload -Uz colors; colors
autoload -Uz compinit; compinit

# Completion
#

# Case-insensitive
zstyle ':completion:*' matcher-list '' 'm:{a-zA-Z}={A-Za-z}'

# https://github.com/zsh-users/zsh-autosuggestions/blob/master/INSTALL.md
source "$(brew --prefix)/share/zsh-autosuggestions/zsh-autosuggestions.zsh"
bindkey '^[[Z' autosuggest-accept

# https://github.com/rupa/z
source "$(brew --prefix)/etc/profile.d/z.sh"

# History
#

setopt hist_ignore_dups hist_ignore_space hist_reduce_blanks share_history

# Prompt
#

setopt prompt_subst

# Use a script from the Git completion system
source "$(brew --prefix)/etc/bash_completion.d/git-prompt.sh"
export GIT_PS1_SHOWDIRTYSTATE=1 GIT_PS1_SHOWSTASHSTATE=1

# Regular expression to trim the path: https://regex101.com/r/yBxF2k/1. FWIW,
# non-printable characters (such as colors) should be wrapped with `%{....%}`
PROMPT='%{${fg[cyan]}%}$(pwd | perl -pe "s|^${HOME}|~|g; s/(\w)[^\/]+\//\1\//g") $ %{${reset_color}%}'
RPROMPT='%{${fg[magenta]}%}$(__git_ps1 "%s")%{${reset_color}%}'

# Aliases
#

# Navigation
alias ..="cd .."
alias ...="cd ../.."
alias ....="cd ../../.."
alias .....="cd ../../../.."

# Replacements
alias grep='egrep --color="auto"'
alias ls="exa"

# Shortcuts
alias b="brew"
alias d="docker"
alias g="git"
alias k="kubectl"
alias ll="ls -l"
alias la="ls -al"
alias v="nvim"

# Functions
#

function bprune() {
  brew uninstall --force --zap "${1}"
}

function _bprune() {
  _alternative "1: :($(brew list))"
}

compdef _bprune bprune

function gupdate() {
  DEFAULT_BRANCH=$(git symbolic-ref refs/remotes/origin/HEAD | sed 's@^refs/remotes/origin/@@')

  git fetch origin "${DEFAULT_BRANCH}:${DEFAULT_BRANCH}"
  git rebase "${DEFAULT_BRANCH}"
}

compdef _kns kns

# Permanently set the Kubernetes namespace.
function kns() {
  kubectl get namespace "${1}" > /dev/null
  [[ "${?}" -ne 0 ]] && return

  kubectl config set-context --current --namespace="${1}"
}

function _kns() {
  _alternative "1: :($(kubectl get namespaces --output=go-template='{{range .items}}{{printf "%s\n" .metadata.name}}{{end}}'))"
}

compdef _kplain kplain

# Pretty print Kubernetes secrets.
function kplain() {
  kubectl get secret "${1}" --output=go-template='{{range $key, $value := .data}}{{printf "%s=%s\n" $key ($value | base64decode)}}{{end}}'
}

function _kplain() {
  _alternative "1: :($(kubectl get secrets --output=go-template='{{range .items}}{{printf "%s\n" .metadata.name}}{{end}}'))"
}

function kpods() {
  kubectl get pods --selector="app.kubernetes.io/name=${1}" "${@:2}"
}

compdef _kwatch kwatch

# Watch Kubernetes resources.
function kwatch() {
  kubectl get "${1}" --watch-only
}

function _kwatch() {
  _alternative "1: :($(kubectl api-resources --output=name))"
}

# Exports
#

export EDITOR="nvim"

# https://github.com/drduh/macOS-Security-and-Privacy-Guide#homebrew
export HOMEBREW_CASK_OPTS="--require-sha"
export HOMEBREW_NO_ANALYTICS="1"
export HOMEBREW_NO_INSECURE_REDIRECT="1"

export LANG="en_US.UTF-8" LC_ALL="en_US.UTF-8"

export PNPM_HOME="${HOME}/Library/pnpm"

export PATH="${PATH}:/Applications/Visual Studio Code.app/Contents/Resources/app/bin"
export PATH="${PATH}:${HOME}/.krew/bin"
export PATH="${PATH}:${HOME}/dev/next/scripts" # TODO(remyduthu): Match subdirectories.
export PATH="${PATH}:$(go env GOPATH)/bin"
export PATH="${PATH}:${PNPM_HOME}"
