# Dotfiles

This project is inspired by [Nyalab](https://github.com/Nyalab/handles), [mathiasbynens](https://github.com/mathiasbynens/dotfiles/) and [paulirish](https://github.com/paulirish/dotfiles) dotfiles.

## Procedure

- [Install a fresh copy of macOS](https://support.apple.com/en-gb/HT212749).
- Perform the inital configuration until you can use the system.
- [Install Dashlane](https://www.dashlane.com/download).
- Download this repository.
- Execute the [`run.zsh`](./run.zsh) script without arguments to configure the entire system.
- Follow the ["Hardening macOS"](https://www.bejarano.io/hardening-macos/) guide. Some parameters are already set but others cannot be configured dynamically.

## Modules

This project is splitted into modules. Each module vaguely represents a tool.

### Homebrew ([`./modules/brew/`](./modules/brew/))

#### Tips and tricks

- Keep only the dependencies listed in the [Brewfile](`./modules/brew/Brewfile`):

  ```
  brew bundle cleanup --file="${DOTFILES_PATH}/modules/brew/Brewfile" --force --zap
  ```

## Todo

- Lint ZSH scripts
- Download Git repositories
- Write `backup.zsh` script to:
  - Save SSH keys
  - Save `kubectl` configuration files (~/.kube)
  - Save pictures (~/Pictures/)
