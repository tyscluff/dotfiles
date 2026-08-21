# dotfiles

Public, version-controlled configuration for my development environment.

## Managed configuration

- Neovim / LazyVim
- GitHub CLI preferences
- Ghostty
- HerdR theme and keybindings
- Pi settings, keybindings, and shared skills

Credentials, sessions, logs, caches, downloaded dependencies, and application databases are intentionally excluded.

## Install on a new Mac

```sh
brew install stow

git clone git@github.com:tyscluff/dotfiles.git ~/dotfiles
cd ~/dotfiles
./install.sh
```

Then authenticate locally:

```sh
gh auth login
pi
# Use /login inside Pi.
```

Install the Pi packages declared in `pi/.pi/agent/settings.json`:

```sh
pi install npm:pi-mcp-adapter
pi install npm:pi-web-access
```

## Updating configuration

Edit files in this repository; the paths under `$HOME` are symlinks created by Stow.

```sh
cd ~/dotfiles
git status
git diff
gitleaks detect --source . --redact
git add -p
git commit -m "Update configuration"
git push
```
