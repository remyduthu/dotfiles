# Dotfiles

This project is inspired by [Nyalab](https://github.com/Nyalab/handles), [mathiasbynens](https://github.com/mathiasbynens/dotfiles/) and [paulirish](https://github.com/paulirish/dotfiles) dotfiles.

## Procedure

- Execute the [`export.zsh`](./export.zsh) script.
- [Install a fresh copy of macOS](https://support.apple.com/en-gb/HT212749).
- Perform the initial configuration until you can use the system.
- Download this repository.
- Execute the [`run.zsh`](./run.zsh) script without arguments to configure the entire system.
- Follow the ["Hardening macOS"](https://www.bejarano.io/hardening-macos/) guide[^*].
- Configure native applications (Mail, Safari, etc.)[^*].

[^*]: Some parameters are already set but others cannot be set programmatically.

## Modules

This project is splitted into modules. Each module vaguely represents a tool.

### Homebrew ([`./modules/brew/`](./modules/brew/))

#### Tips and tricks

- Keep only the dependencies listed in the [Brewfile](`./modules/brew/Brewfile`):

  ```zsh
  brew bundle cleanup --file="${DOTFILES_PATH}/modules/brew/Brewfile" --force --zap
  ```

- List Brew formulae that I've installed by hand:

  ```zsh
  brew list --formulae --full-name --installed-on-request
  ```

## Todo

- Lint ZSH scripts
