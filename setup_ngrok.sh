#!/bin/bash

# 1. Identify the actual user
REAL_USER=${SUDO_USER:-$(whoami)}
USER_HOME=$(getent passwd "$REAL_USER" | cut -d: -f6)
NGROK_PATH=$(command -v ngrok)
CONFIG_FILE="$USER_HOME/.config/ngrok/ngrok.yml"
SERVICE_FILE="/etc/systemd/system/ngrok.service"

# 2. Ask for the Authtoken (Optional check)
# If you already have it in your file, we should keep it. 
# Here we'll try to grab the existing one so we don't lose it.
EXISTING_TOKEN=$(grep "authtoken:" "$CONFIG_FILE" | awk '{print $2}' | tr -d '"')

if [ -z "$EXISTING_TOKEN" ]; then
    echo "No authtoken found. Please paste your ngrok authtoken:"
    read -r EXISTING_TOKEN
fi

# 3. OVERWRITE the config file with the correct format
echo "Writing new configuration to $CONFIG_FILE..."
mkdir -p "$(dirname "$CONFIG_FILE")"
cat <<EOF > "$CONFIG_FILE"
version: "2"
authtoken: $EXISTING_TOKEN
tunnels:
  ssh-service:
    proto: tcp
    addr: 22
EOF

# 4. Update the Systemd Service
echo "Updating service file..."
sudo bash -c "cat <<EOF > $SERVICE_FILE
[Unit]
Description=ngrok background service
After=network.target

[Service]
User=$REAL_USER
ExecStart=$NGROK_PATH start --all --config=$CONFIG_FILE
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF"

# 5. Reload and Restart
sudo systemctl daemon-reload
sudo systemctl restart ngrok.service

echo "------------------------------------------"
echo "Configuration updated and service restarted!"
echo "Your config is now in the 'version: 2' format."
