#!/usr/bin/env zsh

set -eu

autoload -Uz colors; colors

# Create a symbolik link
function link() {
  # -f    Overwrite any existing target
  # -s    Create a symbolic link (instead of a hard link)
  # -v    Be verbose
  ln -fsv "${@}"
}

# Print a formatted task message
function taskf() {
  echo "${fg[blue]}=> [${STAGE}] ${@}${reset_color}"
}

# Print a formatted error message
function errorf() {
  echo "${fg[red]}=> ERROR ${@}${reset_color}"
  exit 1
}

function require() {
  taskf "Test required commands"
  for command in "${@}"
  do
    type "${command}"
  done
}
