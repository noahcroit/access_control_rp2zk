#!/bin/bash
# Installation script for Internet Authen KMITL

# Ensure the script is run with sudo
if [ "$EUID" -ne 0 ]; then
  echo "Please run as root (sudo bash install.sh)"
  exit 1
fi

INSTALL_DIR="/home/pi/Auto-Authen-KMITL"
SERVICE_NAME="internet-authen"

echo "Setting up $SERVICE_NAME..."

# Create the installation directory if it doesn't exist
mkdir -p "$INSTALL_DIR"

# Copy the bash script to the installation directory
cp check_internet.sh "$INSTALL_DIR/"
chmod +x "$INSTALL_DIR/check_internet.sh"
chown pi:pi "$INSTALL_DIR/check_internet.sh"

# Copy systemd files
cp "$SERVICE_NAME.service" /etc/systemd/system/
cp "$SERVICE_NAME.timer" /etc/systemd/system/

# Reload systemd and enable the timer
systemctl daemon-reload
systemctl enable --now "$SERVICE_NAME.timer"

echo "--------------------------------------------------"
echo "Installation complete."
echo "The check script is at: $INSTALL_DIR/check_internet.sh"
echo "The timer is set for every 10 minutes."
echo "--------------------------------------------------"
systemctl status "$SERVICE_NAME.timer"
