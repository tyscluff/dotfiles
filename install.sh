#!/usr/bin/env bash
set -euo pipefail

repo_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)

if ! command -v stow >/dev/null 2>&1; then
  echo "stow is required. Install it with: brew install stow"
  exit 1
fi

cd "$repo_dir"
stow --target "$HOME" config pi agents
