# PiTemplar

![Knight](pik1.png)

PiTemplar is a local cloud NAS operated via Web GUI that is interactive. It offers storage on your Local Area network anytime, anywhere!

First step is obviously the hardware. 

https://a.co/d/fTyeqv4     Raspberry pi Zero 2W

https://a.co/d/5Apdn16     Upgraded heatsink

https://a.co/d/bW6hi50     Screen, makes it more fun

https://a.co/d/inzVWE7     Pisugar 3 battery, optional, but highly recommended. Makes it a true mobile server.

Installation begins simply by downloading RaspberryPiImager, you want to use a Pi OS Lite for command line only. That's all you'll need.

For this specific project, I named everything either PiTemplar or templar. so default username PiTemplar, default password pitemplar, device name PiTemplar. Feel free to make modifications but for initial setup purposes let's stick to this. Set up SSH as well with those credentials so you have an easy reference starting point and noo concerns over remembering credentials. The initial network can be either your home network, or setup a hotspot on your phone with SSID PiTemplar and password pitemplar initially then add your network on the web GUI once established. See the pattern here? Moving on...

Once RaspberryPiOS Lite is installed (32 or 64 bit, doesn't really matter), Let's begin configuring the Pi to make components work. 

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

upload all files to the same python folder. once you've done that, start the below steps.

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

Once all is verified and good to go, let's do SAMBA to make it work as a true NAS

sudo apt update
sudo apt install -y samba samba-common-bin

once that install is done, do the smbclient

sudo apt update
sudo apt install -y smbclient

Verify: 

smbd --version


create the share

mkdir /srv/templar/shares/private
chmod 770 /srv/templar/shares/private

sudo cp /etc/samba/smb.conf /etc/samba/smb.conf.bak  (maybe pull it to your drive via ftp)

Edit Samba config
sudo nano /etc/samba/smb.conf

Replace everything below [global] with this:
[global]
   workgroup = WORKGROUP
   server string = PiTemplar NAS
   netbios name = PITEMPLAR
   security = user
   map to guest = Bad User
   dns proxy = no
   log file = /var/log/samba/log.%m
   max log size = 1000

[private]
   path = /srv/templar/shares/private
   browseable = yes
   writable = yes
   guest ok = no
   read only = no
   valid users = templar

Save and exit

Create Samba user

Even though templar exists, Samba needs its own password.

sudo smbpasswd -a templar
sudo smbpasswd -e templar

Restart and enable Samba
sudo systemctl restart smbd
sudo systemctl enable smbd

systemctl status smbd

Test from another device
Windows
\\templar\private

macOS / Linux
smb://templar/private


🎩 Thank You ♥
💖 Support Me
If you like my work and want to support me, plz consider

https://www.paypal.me/Modernknight101

or buy a copy or my sci-fi book, available on Amazon

https://a.co/d/hx5OLOO Gods Among Us: Alienthology

