#!/bin/bash
set -e

APP_DIR="/home/ec2-user/my_photo_app"
APP_USER="ec2-user"

echo "Running setup_deployment_dir.sh as $(whoami)"

# Ensure the parent directory exists
echo "Ensuring /home/ec2-user exists..."
mkdir -p /home/ec2-user || { echo "ERROR: Could not create /home/ec2-user. Exiting."; exit 1; }
chown $APP_USER:$APP_USER /home/ec2-user || { echo "ERROR: Could not chown /home/ec2-user. Exiting."; exit 1; }
chmod 755 /home/ec2-user || { echo "ERROR: Could not chmod /home/ec2-user. Exiting."; exit 1; }

# Ensure the application directory exists and is owned by the app user
echo "Ensuring application directory $APP_DIR exists and is owned by $APP_USER..."
mkdir -p "$APP_DIR" || { echo "ERROR: Could not create $APP_DIR. Exiting."; exit 1; }
chown -R $APP_USER:$APP_USER "$APP_DIR" || { echo "ERROR: Could not chown $APP_DIR. Exiting."; exit 1; }
chmod -R 755 "$APP_DIR" || { echo "ERROR: Could not chmod $APP_DIR. Exiting."; exit 1; }

echo "Deployment directory setup complete."