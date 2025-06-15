#!/bin/bash
set -e # Exit immediately if a command exits with a non-zero status

# This script is designed to be run as 'ec2-user' by CodeDeploy
APP_DIR="/home/ec2-user/my_photo_app"

echo "Navigating to app directory: $APP_DIR"
cd "$APP_DIR" || { echo "ERROR: Failed to change directory to $APP_DIR. Exiting."; exit 1; }

echo "Activating virtual environment..."
# Check if .venv/bin/activate exists before sourcing
if [ -f ".venv/bin/activate" ]; then
  # Use '.' command for broader shell compatibility during sourcing
  . .venv/bin/activate || { echo "ERROR: Failed to activate venv. Exiting."; exit 1; }
  echo "Virtual environment activated successfully."
else
  echo "ERROR: .venv/bin/activate not found. This indicates the virtual environment was not deployed correctly. Exiting."
  exit 1
fi

# IMPORTANT: Since pip install is done in CodeBuild and .venv is packaged,
# you typically do NOT need to run 'pip install -r requirements.txt' here again.
# If you run it here, it will re-download and re-install dependencies on every deployment,
# which is inefficient.

# Add other setup steps here if needed, e.g., database migrations.
# Example: python3 manage.py migrate