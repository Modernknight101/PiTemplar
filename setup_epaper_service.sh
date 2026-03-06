#!/bin/bash

# -------------------------------------------------------

# PiTemplar ePaper Auto-Start Setup

# Automates systemd service creation

# -------------------------------------------------------

USER="pitemplar"
SCRIPT="/home/pitemplar/e-Paper/RaspberryPi_JetsonNano/python/PiTemplar/mem_display.py"
SERVICE="/etc/systemd/system/epaper-status.service"

echo "----------------------------------------"
echo "1️⃣ Making mem_display.py executable..."

chmod +x "$SCRIPT"

echo "----------------------------------------"
echo "2️⃣ Creating systemd service..."

sudo tee "$SERVICE" > /dev/null <<EOF
[Unit]
Description=Waveshare ePaper System Status
After=multi-user.target

[Service]
Type=simple
User=pitemplar
WorkingDirectory=/home/pitemplar/e-Paper/RaspberryPi_JetsonNano/python/PiTemplar
ExecStart=/usr/bin/python3 /home/pitemplar/e-Paper/RaspberryPi_JetsonNano/python/PiTemplar/mem_display.py
Restart=always
RestartSec=10
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
EOF

echo "Service file created."

echo "----------------------------------------"
echo "3️⃣ Reloading systemd..."

sudo systemctl daemon-reexec
sudo systemctl daemon-reload

echo "----------------------------------------"
echo "4️⃣ Enabling service at boot..."

sudo systemctl enable epaper-status.service

echo "----------------------------------------"
echo "5️⃣ Starting service..."

sudo systemctl start epaper-status.service

echo "----------------------------------------"
echo "6️⃣ Checking service status..."

systemctl status epaper-status.service --no-pager

echo "----------------------------------------"
echo "✅ Setup complete!"
echo ""
echo "Your e-paper display should update within ~30 seconds."
echo ""
echo "To check status later:"
echo "systemctl status epaper-status.service"
