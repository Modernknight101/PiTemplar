#!/bin/bash

# -------------------------------------------------------------------

# PiTemplar Web GUI Setup Script

# Installs dependencies, fixes permissions, sets up sudoers, and systemd

# -------------------------------------------------------------------

# Paths

WEB_GUI_DIR="/home/pitemplar/e-Paper/RaspberryPi_JetsonNano/python/PiTemplar"
WEB_GUI_SCRIPT="$WEB_GUI_DIR/web_gui.py"
SERVICE_FILE="/etc/systemd/system/web_gui.service"
SUDOERS_FILE="/etc/sudoers.d/pitemplar_webgui"

echo "----------------------------------------"
echo "1️⃣ Installing Python3 and Flask..."
sudo apt update
sudo apt install -y python3-full python3-venv python3-flask dos2unix

echo "----------------------------------------"
echo "2️⃣ Fixing line endings for web_gui.py..."
sudo dos2unix "$WEB_GUI_SCRIPT"

echo "----------------------------------------"
echo "3️⃣ Making script executable..."
sudo chmod +x "$WEB_GUI_SCRIPT"

echo "----------------------------------------"
echo "4️⃣ Configuring sudo permissions for web GUI..."

REBOOT_PATH=$(which reboot)
SHUTDOWN_PATH=$(which shutdown)
NMCLI_PATH=$(which nmcli)
IP_PATH=$(which ip)
IFCONFIG_PATH=$(which ifconfig)

if [ ! -f "$SUDOERS_FILE" ]; then
sudo tee "$SUDOERS_FILE" > /dev/null <<EOL
pitemplar ALL=(ALL) NOPASSWD: $REBOOT_PATH
pitemplar ALL=(ALL) NOPASSWD: $SHUTDOWN_PATH
pitemplar ALL=(ALL) NOPASSWD: $NMCLI_PATH
pitemplar ALL=(ALL) NOPASSWD: $IP_PATH
pitemplar ALL=(ALL) NOPASSWD: $IFCONFIG_PATH
EOL

```
sudo chmod 440 "$SUDOERS_FILE"
echo "Sudoers rules created."
```

else
echo "Sudoers rules already exist. Skipping."
fi

echo "----------------------------------------"
echo "5️⃣ Creating systemd service..."
sudo tee "$SERVICE_FILE" > /dev/null <<EOL
[Unit]
Description=Raspberry Pi E-Paper Web GUI
After=network.target

[Service]
Type=simple
User=pitemplar
WorkingDirectory=$WEB_GUI_DIR
ExecStart=/usr/bin/python3 $WEB_GUI_SCRIPT
Restart=always
RestartSec=5
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
EOL

echo "----------------------------------------"
echo "6️⃣ Reloading systemd..."
sudo systemctl daemon-reload

echo "7️⃣ Enabling service to start on boot..."
sudo systemctl enable web_gui.service

echo "8️⃣ Starting web_gui service..."
sudo systemctl restart web_gui.service

echo "----------------------------------------"
echo "9️⃣ Checking service status..."
sudo systemctl status web_gui.service --no-pager

echo "----------------------------------------"
echo "✅ Setup complete!"
echo "Access the web GUI at:"
echo "http://<YOUR_PI_IP>:8080"
