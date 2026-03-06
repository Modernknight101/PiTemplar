#!/bin/bash

# -------------------------------------------------------

# PiTemplar ePaper Auto-Start Setup

# Automates crontab + systemd service creation

# -------------------------------------------------------

USER="pitemplar"
SCRIPT="/home/pitemplar/e-Paper/RaspberryPi_JetsonNano/python/PiTemplar/mem_display.py"
SERVICE="/etc/systemd/system/epaper-status.service"

echo "----------------------------------------"
echo "1️⃣ Making mem_display.py executable..."

chmod +x "$SCRIPT"

echo "----------------------------------------"
echo "2️⃣ Adding @reboot cron job..."

CRON_ENTRY="@reboot python3 $SCRIPT"

(crontab -u $USER -l 2>/dev/null | grep -v "$SCRIPT"; echo "$CRON_ENTRY") | crontab -u $USER -

echo "Cron job installed."

echo "----------------------------------------"
echo "3️⃣ Creating systemd service..."

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
echo "4️⃣ Reloading systemd..."

sudo systemctl daemon-reexec
sudo systemctl daemon-reload

echo "----------------------------------------"
echo "5️⃣ Enabling service at boot..."

sudo systemctl enable epaper-status.service

echo "----------------------------------------"
echo "6️⃣ Starting service..."

sudo systemctl start epaper-status.service

echo "----------------------------------------"
echo "7️⃣ Checking service status..."

systemctl status epaper-status.service --no-pager

echo "----------------------------------------"
echo "✅ Setup complete!"
echo ""
echo "Your e-paper display should update within ~30 seconds."
echo ""
echo "To check status later:"
echo "systemctl status epaper-status.service"
