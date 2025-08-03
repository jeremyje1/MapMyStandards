#!/bin/bash
set -e

echo "Setting up Python environment for Railway deployment..."

# Create virtual environment if it doesn't exist
if [ ! -d "/opt/venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv /opt/venv
fi

# Activate virtual environment
source /opt/venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install requirements
echo "Installing requirements..."
pip install -r requirements.txt

echo "Setup complete!"
