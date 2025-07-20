# Dotfiles

This repository contains my personal dotfiles and setup scripts for macOS.
It is inspired by the dotfiles of [Nyalab](https://github.com/Nyalab/handles), [mathiasbynens](https://github.com/mathiasbynens/dotfiles/), and [paulirish](https://github.com/paulirish/dotfiles).

## Procedure

1. **Export your current configuration**

   Run [`export.zsh`](./export.zsh) to back up your system configuration (SSH keys, etc.).

2. **Install macOS**

   [Reinstall macOS](https://support.apple.com/en-gb/HT212749) if needed.

3. **Initial macOS configuration**

   Complete the basic setup until you can access the system.

4. **Clone this repository**

```sh
git clone https://github.com/remyduthu/dotfiles.git
cd dotfiles
```

5. **Run the setup script**

   Execute [`run.zsh`](./run.zsh) with no arguments.
   This will install Homebrew and configure your system automatically.

6. **Apply manual macOS preferences**

   Follow the [macOS configuration](#macos-configuration) steps below to fine-tune your system.

## macOS Configuration

Below are my recommended macOS settings.
Adjust them as needed.
Some are automated by the [system module](./modules/system/install.zsh).
For security, I referenced the ["Hardening macOS"](https://www.bejarano.io/hardening-macos/) guide.

<details>
<summary>Finder</summary>

- Preferences
  - New Finder windows show: Home
  - Advanced
    - Show all filename extensions: On
    - Keep folders on top:
    - In windows when sorting by name: On
    - On Desktop: On
- View
  - as List
  - Show Path Bar: On
  - Show Status Bar: On

</details>

<details>
<summary>System Settings</summary>

- Network
  - Firewall: On
- General
  - Software Update: Enable all automatic updates
  - Sharing: Disable all sharing options
- Desktop & Dock
  - Size: Small
  - Magnification: Off
  - Automatically hide and show the Dock: On
  - Animate opening applications: Off
  - Show suggested and recent applications in Dock: Off
- Lock Screen
  - Turn display off on battery when inactive: 5 minutes
  - Turn display off on power when inactive: 5 minutes
  - Require password after screen saver or display sleep: Immediately
- Users & Groups
  - Guest User: Off
- Privacy & Security
  - Allow applications from: App Store & Known Developers
  - FileVault: On
- Keyboard
  - Key repeat rate: Fast
  - Delay until repeat: Short
  - Turn keyboard backlight off after inactivity: After 5 seconds
- Trackpad
  - Tap to click: On

</details>

## Todo

- [ ] Lint ZSH scripts

---

Feel free to fork and adapt these dotfiles to your own workflow!
