#!/bin/bash
echo "Stopping Streamlit app..."
# Use '|| true' to prevent script from failing if the service isn't running (e.g., first deployment)
sudo systemctl stop streamlit_app || true
echo "Streamlit app stopped."