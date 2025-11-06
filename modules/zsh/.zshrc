# `.zshrc` is sourced in interactive shells
# (https://zsh.sourceforge.io/Contrib/startup/)

# ZSH options: http://zsh.sourceforge.net/Doc/Release/Options.html

export DOTFILES_PATH="/Users/remyduthu/dev/dotfiles/"

# Add Brew completion files. It must be done before `compinit` is called
# (https://docs.brew.sh/Shell-Completion#configuring-completions-in-zsh).
if type brew &>/dev/null
then
  FPATH="$(brew --prefix)/share/zsh/site-functions:${FPATH}"
fi

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

# Enable vi mode.
bindkey -v

# https://github.com/rupa/z
source "$(brew --prefix)/etc/profile.d/z.sh"

# https://github.com/junegunn/fzf?tab=readme-ov-file#setting-up-shell-integration
source <(fzf --zsh)
export FZF_COMPLETION_OPTS='--border --height=25% --info=inline'

# History
#
# https://martinheinz.dev/blog/110

HIST_STAMPS="yyyy-mm-dd"
HISTFILE="${HOME}/.zsh_history"
setopt append_history        # Append to history file (default)
setopt extended_history      # Write the history file in the ':start:elapsed;command' format.
setopt hist_ignore_all_dups  # Delete an old recorded event if a new event is a duplicate.
setopt hist_ignore_dups      # Do not record an event that was just recorded again.
setopt hist_ignore_space     # Do not record an event starting with a space.
setopt hist_no_store         # Don't store history commands
setopt hist_reduce_blanks    # Remove superfluous blanks from each command line being added to the history.
setopt hist_save_no_dups     # Do not write a duplicate event to the history file.
setopt hist_verify           # Do not execute immediately upon history expansion.
setopt inc_append_history    # Write to the history file immediately, not when the shell exits.
setopt share_history         # Share history between all sessions.


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
alias cat='bat'
alias grep='egrep --color="auto"'
alias ls="eza"

# Shortcuts
alias b="brew"
alias d="docker"
alias g="git"
alias k="kubectl"
alias la="ls -al"
alias ll="ls -l"
alias v="nvim"
alias zs="source ${HOME}/.zshrc"

# Functions
#

function bprune() {
  brew uninstall --force --zap "${1}"
}

function _bprune() {
  _alternative "1: :($(brew list))"
}

compdef _bprune bprune

CODE_WORKSPACES_PATH="${DOTFILES_PATH}/modules/code/workspaces/"

function cwork() {
  if [[ "${1}" != "." ]]; then
    code "${CODE_WORKSPACES_PATH}/${1}.code-workspace"
    return
  fi

  local current_directory="${PWD}"
  local dev_directory="${HOME}/dev/"

  if [[ "${current_directory}" != "${dev_directory}"* ]]; then
    echo "'.' can only be used inside the '${dev_directory}' directory."
    return 1
  fi

  code "${CODE_WORKSPACES_PATH}/${current_directory#"${dev_directory}"}.code-workspace"
}

function _cwork() {
  _alternative "1: :($(find "${CODE_WORKSPACES_PATH}/" -name '*.code-workspace' -type f | sed "s|${CODE_WORKSPACES_PATH}/||; s/\.code-workspace$//"))"
}

compdef _cwork cwork

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

# Pretty print Kubernetes JSON logs.
function kjlogs() {
  kubectl logs "${@}"|jq -R 'fromjson? | .'
}

function _kjlogs() {
  _alternative "1: :($(kubectl get pods --output=go-template='{{range .items}}{{printf "%s\n" .metadata.name}}{{end}}'))"
}

compdef _kjlogs kjlogs

# Exports
#

export EDITOR="nvim"

# https://github.com/drduh/macOS-Security-and-Privacy-Guide#homebrew
export HOMEBREW_CASK_OPTS="--require-sha"
export HOMEBREW_NO_ANALYTICS="1"
export HOMEBREW_NO_INSECURE_REDIRECT="1"

export LANG="en_US.UTF-8" LC_ALL="en_US.UTF-8"

# https://github.com/nvm-sh/nvm?tab=readme-ov-file#installing-and-updating
export NVM_DIR="${HOME}/.nvm"
[ -s "/opt/homebrew/opt/nvm/nvm.sh" ] && \. "/opt/homebrew/opt/nvm/nvm.sh"  # Load nvm.
[ -s "/opt/homebrew/opt/nvm/etc/bash_completion.d/nvm" ] && \. "/opt/homebrew/opt/nvm/etc/bash_completion.d/nvm"  # Load nvm completion.

export PNPM_HOME="${HOME}/Library/pnpm"

export PYENV_ROOT="${HOME}/.pyenv"
eval "$(pyenv init - zsh)"

export PATH="${PATH}:/Applications/Visual Studio Code.app/Contents/Resources/app/bin"
export PATH="${PATH}:/opt/homebrew/bin"
export PATH="${PATH}:/opt/homebrew/opt/libpq/bin"
export PATH="${PATH}:/opt/homebrew/sbin"
export PATH="${PATH}:$(go env GOPATH)/bin"
export PATH="${PATH}:${HOME}/.krew/bin"
export PATH="${PATH}:${HOME}/.local/bin"
export PATH="${PATH}:${PNPM_HOME}"
export PATH="${PATH}:${PYENV_ROOT}/bin"

if [ -d "/opt/homebrew/opt/ruby/bin" ]; then
  export PATH="/opt/homebrew/opt/ruby/bin:${PATH}"
  export PATH=`gem environment gemdir`/bin:${PATH}
fi

# Include Google Cloud SDK.
source "/opt/homebrew/share/google-cloud-sdk/path.zsh.inc"

# Use GNU binaries installed by Homebrew instead of those provided by macOS.
for gnubin in gnu-sed grep findutils coreutils; do
    export PATH="${PATH}:/opt/homebrew/opt/${gnubin}/libexec/gnubin"
done

export WORDCHARS="*?.[]~=&;!#$%^(){}<>"
