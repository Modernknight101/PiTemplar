# PiTemplar

![Knight](pik1.png)

PiTemplar is a local cloud NAS operated via Web GUI that is interactive. It offers storage on your Local Area network anytime, anywhere!

Installation begins simply by downloading RaspberryPiImager, you want to use a Pi OS Lite for command line only. That's all you'll need.

I configured this device using a Waveshare e-paper screen.

Waveshare e-paper uses SPI.

sudo raspi-config


Go to:

Interface Options → SPI → Enable


Reboot:

sudo reboot

Install Waveshare e-Paper library

Install dependencies first:

sudo apt update
sudo apt install -y python3-pip python3-pil python3-numpy git
pip3 install psutil


Clone Waveshare’s repo:

git clone https://github.com/waveshareteam/e-Paper.git
cd e-Paper/RaspberryPi_JetsonNano/python/examples/
python3 epd_2in13_V4_test.py


Your drivers will be here:

~/e-Paper/RaspberryPi_JetsonNano/python

Identify your exact screen model (I used Waveshare v4)

Since you said v4, it’s usually one of these:

epd2in13_V4

epd2in9_V2

epd4in2_V2

Most Pi Zero projects use 2.13" v4, so I’ll assume:

epd2in13_V4

Now upload the mem_display.py to your python folder

From the driver directory:

cd ~/e-Paper/RaspberryPi_JetsonNano/python
python3 mem_display.py


You should now see:

RAM STATUS
Used: XXX MB
Total: XXX MB
YY% Used

Start on boot

Edit crontab:

crontab -e


Add:

reboot python3 /home/templar/e-Paper/RaspberryPi_JetsonNano/python/mem_display.py 

⚠️ Important e-Paper Notes

Do NOT refresh too fast (≤30s is good)

Frequent refreshes shorten panel life

Waveshare e-paper is slow by design — that’s normal

sudo apt update 

sudo apt install -y python3-psutil

 Make sure the script is executable (recommended)

chmod +x /home/templar/e-Paper/RaspberryPi_JetsonNano/python/mem_display.py

Create a systemd service file

sudo nano /etc/systemd/system/epaper-status.service

Paste exactly this (adjust nothing unless noted):

[Unit]
Description=Waveshare ePaper System Status
After=multi-user.target

[Service]
Type=simple
User=templar
WorkingDirectory=/home/templar/e-Paper/RaspberryPi_JetsonNano/python
ExecStart=/usr/bin/python3 /home/templar/e-Paper/RaspberryPi_JetsonNano/python/mem_display.py
Restart=always
RestartSec=10
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target


Save:

CTRL+O → ENTER
CTRL+X

Reload systemd and enable the service
sudo systemctl daemon-reexec
sudo systemctl daemon-reload
sudo systemctl enable epaper-status.service

Start it now (no reboot needed)
sudo systemctl start epaper-status.service

Within ~30 seconds, your e-paper should update.

Check status (VERY useful)
systemctl status epaper-status.service


You should see:

Active: active (running)

No red error messages

To see logs:

journalctl -u epaper-status.service -f

🔁 Reboot test (important)
sudo reboot

After boot:

Wait ~30–60 seconds

Screen should refresh automatically

If it does → you’re done ✅

🧠 Common Gotchas (you’re already safe)

✅ Uses full path to python3

✅ Runs as user templar (SPI access OK)

✅ Working directory set (imports work)

✅ Restart enabled if script crashes


Now that the screen works, let's do web GUI next!

Here’s a step-by-step guide for your web GUI.

1️⃣ Create a systemd service file

Run:

sudo nano /etc/systemd/system/web_gui.service


Paste this:

[Unit]
Description=Raspberry Pi E-Paper Web GUI
After=network.target

[Service]
Type=simple
User=templar
WorkingDirectory=/home/templar/e-Paper/RaspberryPi_JetsonNano/python
ExecStart=/usr/bin/python3 web_gui.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target


Important:

Replace User=templar with your username if different.

Make sure WorkingDirectory points to the folder where web_gui.py lives.

Make sure the path to Python matches your system (which python3 → usually /usr/bin/python3).

2️⃣ Reload systemd to recognize the new service
sudo systemctl daemon-reload

3️⃣ Enable it to start at boot
sudo systemctl enable web_gui.service

4️⃣ Start the service now
sudo systemctl start web_gui.service

5️⃣ Check status
sudo systemctl status web_gui.service


You should see something like:

Active: active (running) since ...

