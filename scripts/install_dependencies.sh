#!/bin/bash
set -e # Exit immediately if a command exits with a non-zero status

APP_DIR="/home/ec2-user/my_photo_app"

echo "Current user: $(whoami)"
echo "Deployment target directory: $APP_DIR"

# Navigate to the app directory
echo "Navigating to app directory: $APP_DIR"
cd "$APP_DIR" || { echo "ERROR: Failed to change directory to $APP_DIR. Exiting."; exit 1; }
echo "Current working directory: $(pwd)"

# Create the virtual environment
echo "Creating virtual environment..."
python3 -m venv .venv || { echo "ERROR: Failed to create venv. Exiting."; exit 1; }
echo "Virtual environment created."

# Activate the virtual environment
ACTIVATE_SCRIPT=".venv/bin/activate"
echo "Activating virtual environment..."
. "$ACTIVATE_SCRIPT" || { echo "ERROR: Failed to activate venv using '$ACTIVATE_SCRIPT'. Exiting."; exit 1; }
echo "Virtual environment activated successfully."

# Install Python dependencies into the virtual environment
echo "Installing Python dependencies (pip install -r requirements.txt)..."
pip install -r requirements.txt || { echo "ERROR: Failed to install dependencies. Exiting."; exit 1; }
echo "Python dependencies installed successfully."

# Verify Python path and pip (for debugging)
echo "Python executable in venv: $(which python)"
echo "Pip executable in venv: $(which pip)"

echo "Dependencies installation complete."