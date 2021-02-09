# Dotfiles

This project is inspired by [Nyalab](https://github.com/Nyalab/handles), [mathiasbynens](https://github.com/mathiasbynens/dotfiles/) and [paulirish](https://github.com/paulirish/dotfiles) dotfiles.

## Modules

This project is splitted into modules. Each module vaguely represents a tool.

### Homebrew ([`./modules/brew/`](./modules/brew/))

#### Tips and tricks

- Keep only the dependencies listed in the [Brewfile](`./modules/brew/Brewfile`):

  ```
  brew bundle cleanup --file="${DOTFILES_PATH}/modules/brew/Brewfile" --force --zap
  ```

## Todo

- Apply a formatter (.editorconfig)?
- SSH — How to save SSH keys?
- Configure iTerm profiles
- http://stratus3d.com/blog/2015/02/28/sync-iterm2-profile-with-dotfiles-repository/
