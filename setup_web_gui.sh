#!/bin/bash
# -------------------------------------------------------------------
# PiTemplar Web GUI Setup Script
# Installs dependencies, fixes permissions, sets up sudoers, and systemd
# -------------------------------------------------------------------

# Paths
WEB_GUI_DIR="/home/pitemplar/e-Paper/RaspberryPi_JetsonNano/python/PiTemplar"
WEB_GUI_SCRIPT="$WEB_GUI_DIR/web_gui.py"
SERVICE_FILE="/etc/systemd/system/web_gui.service"
SUDOERS_FILE="/etc/sudoers.d/pitemplar_shutdown"

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
echo "3.5️⃣ Configuring reboot permission for pitemplar..."
SHUTDOWN_PATH=$(which shutdown)

if [ ! -f "$SUDOERS_FILE" ]; then
    echo "pitemplar ALL=(ALL) NOPASSWD: $SHUTDOWN_PATH" | sudo tee "$SUDOERS_FILE" > /dev/null
    sudo chmod 440 "$SUDOERS_FILE"
    echo "Sudoers entry created."
else
    echo "Sudoers entry already exists. Skipping."
fi

echo "----------------------------------------"
echo "4️⃣ Creating systemd service..."
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
echo "5️⃣ Reloading systemd..."
sudo systemctl daemon-reload

echo "6️⃣ Enabling service to start on boot..."
sudo systemctl enable web_gui.service

echo "7️⃣ Starting web_gui service..."
sudo systemctl restart web_gui.service

echo "----------------------------------------"
echo "8️⃣ Checking service status..."
sudo systemctl status web_gui.service --no-pager

echo "----------------------------------------"
echo "Setup complete! Access the web GUI at http://<YOUR_PI_IP>:8080"