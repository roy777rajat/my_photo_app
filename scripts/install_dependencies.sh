#!/bin/bash
set -e # Exit immediately if a command exits with a non-zero status

# This script is designed to be run as 'ec2-user' by CodeDeploy
APP_DIR="/home/ec2-user/my_photo_app"

echo "Current user: $(whoami)"
echo "Deployment target directory: $APP_DIR"

# Navigate to the app directory
echo "Navigating to app directory: $APP_DIR"
cd "$APP_DIR" || { echo "ERROR: Failed to change directory to $APP_DIR. Exiting."; exit 1; }
echo "Current working directory: $(pwd)"

# List contents of the current directory to verify file presence
echo "Listing contents of $APP_DIR:"
ls -la "$APP_DIR"

# Check for .venv directory
echo "Checking for .venv directory..."
if [ -d ".venv" ]; then
  echo ".venv directory found."
  echo "Listing contents of .venv:"
  ls -la ".venv/"
  echo "Listing contents of .venv/bin:"
  ls -la ".venv/bin/"
else
  echo "ERROR: .venv directory NOT found at $APP_DIR/.venv. Exiting."
  exit 1
fi

# Check for activate script
ACTIVATE_SCRIPT=".venv/bin/activate"
echo "Checking for activate script: $ACTIVATE_SCRIPT"
if [ -f "$ACTIVATE_SCRIPT" ]; then
  echo "Activate script found: $ACTIVATE_SCRIPT"
  # Check permissions of activate script
  echo "Permissions of activate script: $(ls -l $ACTIVATE_SCRIPT | awk '{print $1}')"
  # Attempt to activate the virtual environment
  echo "Activating virtual environment..."
  . "$ACTIVATE_SCRIPT" || { echo "ERROR: Failed to activate venv using '$ACTIVATE_SCRIPT'. Exiting."; exit 1; }
  echo "Virtual environment activated successfully."
  # Verify Python path and pip
  echo "Python executable in venv: $(which python)"
  echo "Pip executable in venv: $(which pip)"
else
  echo "ERROR: Activate script NOT found at $APP_DIR/$ACTIVATE_SCRIPT. Exiting."
  exit 1
fi

echo "Dependencies installation check complete."