
#!/bin/bash
# -------------------------------------------------------------------
# PiTemplar Web GUI Setup Script
# Installs dependencies, fixes permissions, and sets up systemd service
# -------------------------------------------------------------------

# Paths
WEB_GUI_DIR="/home/pitemplar/e-Paper/RaspberryPi_JetsonNano/python/PiTemplar"
WEB_GUI_SCRIPT="$WEB_GUI_DIR/web_gui.py"
SERVICE_FILE="/etc/systemd/system/web_gui.service"

# 1️⃣ Update system and install Python3 and dependencies
echo "Installing Python3 and Flask..."
sudo apt update
sudo apt install -y python3-full python3-venv python3-flask dos2unix

# 2️⃣ Fix line endings (Windows → Linux)
echo "Fixing line endings for web_gui.py..."
sudo dos2unix "$WEB_GUI_SCRIPT"

# 3️⃣ Make script executable
echo "Setting executable permissions..."
sudo chmod +x "$WEB_GUI_SCRIPT"

# 4️⃣ Create systemd service file
echo "Creating systemd service..."
sudo tee "$SERVICE_FILE" > /dev/null <<EOL
[Unit]
Description=Raspberry Pi E-Paper Web GUI
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=$WEB_GUI_DIR
ExecStart=/usr/bin/python3 $WEB_GUI_SCRIPT
Restart=always
RestartSec=5
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
EOL

# 5️⃣ Reload systemd and enable/start service
echo "Reloading systemd..."
sudo systemctl daemon-reload

echo "Enabling service to start on boot..."
sudo systemctl enable web_gui.service

echo "Starting web_gui service..."
sudo systemctl restart web_gui.service

# 6️⃣ Show status
echo "Service status:"
sudo systemctl status web_gui.service --no-pager

echo "Setup complete! You can access the web GUI at http://<YOUR_PI_IP>:8080"
