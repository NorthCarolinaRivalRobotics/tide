#!/bin/bash

# Exit immediately if a command exits with a non-zero status.
set -e

# Install uv
echo "Installing uv..."
curl -LsSf https://astral.sh/uv/install.sh | sh

# Add uv to PATH for the current session
# The installer script typically advises adding this to .bashrc or .zshrc
# For a non-interactive script, we source the env file directly
source "$HOME/.cargo/env"

# Alternatively, if you know the uv binary path (e.g., if installed to ~/.local/bin)
# export PATH="$HOME/.local/bin:$PATH"

# Verify uv installation (optional)
echo "Verifying uv installation..."
uv --version

# Sync dependencies
echo "Syncing dependencies with uv..."
uv sync

echo "Setup complete."
