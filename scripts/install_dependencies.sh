#!/bin/bash
# This script is designed to be run as 'ec2-user' by CodeDeploy
APP_DIR="/home/ec2-user/my_photo_app"

echo "Navigating to app directory: $APP_DIR"
cd "$APP_DIR" || { echo "ERROR: Failed to change directory to $APP_DIR. Exiting."; exit 1; }

echo "Activating virtual environment..."
source .venv/bin/activate || { echo "ERROR: Failed to activate venv. Exiting."; exit 1; }

echo "Installing/updating Python dependencies (pip install -r requirements.txt)..."
pip install -r requirements.txt || { echo "ERROR: Failed to install dependencies"; exit 1; }
echo "Python dependencies installed successfully."
deactivate