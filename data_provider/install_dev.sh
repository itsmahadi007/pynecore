#!/bin/bash
# Install the package in development mode

set -e

echo "Installing pynecore-data-provider in development mode..."

# Create a virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python -m venv venv
fi

# Activate the virtual environment
source venv/bin/activate

# Install the package in development mode with all extras
pip install -e ".[all]"

echo "Installation complete!"
echo "You can now use the 'pyne-data' command."