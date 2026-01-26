# PiTemplar

![Knight](pik1.png)

PiTemplar is a local cloud NAS operated via Web GUI that is interactive. It offers storage on your Local Area network anytime, anywhere!

First step is obviously the hardware. 

https://a.co/d/fTyeqv4     Raspberry pi Zero 2W

https://a.co/d/5Apdn16     Upgraded heatsink

https://a.co/d/bW6hi50     Screen, makes it more fun

https://a.co/d/inzVWE7     Pisugar 3 battery, optional, but highly recommended. Makes it a true mobile server.

Installation begins simply by downloading RaspberryPiImager, you want to use a Pi OS Lite for command line only. That's all you'll need.

For this specific project, I named everything either PiTemplar or templar. so default username PiTemplar, default password pitemplar, device name PiTemplar. Feel free to make modifications but for initial setup purposes let's stick to this. Set up SSH as well with those credentials so you have an easy reference starting point and no concerns over remembering credentials. The initial network can be either your home network, or setup a hotspot on your phone with SSID PiTemplar and password pitemplar initially then add your network on the web GUI once established. See the pattern here? Moving on...

Once RaspberryPiOS Lite is installed (32 preferably, doesn't really matter), Let's begin configuring the Pi to make components work. 

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

sudo apt install python3-psutil


Clone Waveshare’s repo:

git clone https://github.com/waveshareteam/e-Paper.git
cd e-Paper/RaspberryPi_JetsonNano/python/examples/
python3 epd_2in13_V4_test.py

Your drivers will be here:

~/e-Paper/RaspberryPi_JetsonNano/python

so make sure you are in /home/pitemplar/e-Paper/RaspberryPi_JetsonNano/python/

cd /home/pitemplar/e-Paper/RaspberryPi_JetsonNano/python/

Now clone the pitemplar repository 

git clone https://github.com/Modernknight101/PiTemplar.git

From the driver directory:

cd ~/e-Paper/RaspberryPi_JetsonNano/python/PiTemplar
python3 mem_display.py


You should now see:

Disk Used:
Wifi:
IP:
CPU:

Start on boot

Edit crontab:

crontab -e

no crontab for pitemplar - using an empty one Select an editor. To change later, run select-editor again. 1. /bin/nano <---- easiest 2. /usr/bin/vim.tiny 3. /bin/ed Choose 1-3 [1]:

pick option 1

Add:

@reboot python3 /home/templar/e-Paper/RaspberryPi_JetsonNano/python/PiTemplar/mem_display.py 

 Make sure the script is executable (recommended)

chmod +x /home/pitemplar/e-Paper/RaspberryPi_JetsonNano/python/PiTemplar/mem_display.py

Create a systemd service file

sudo nano /etc/systemd/system/epaper-status.service

Paste exactly this (adjust nothing unless noted):

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

● epaper-status.service - Waveshare ePaper System Status
     Loaded: loaded (/etc/systemd/system/epaper-status.service; enabled; preset: enabled)
     Active: active (running) since Fri 2026-01-23 22:35:35 MST; 29min ago
 Invocation: 1cae31d444084afa96ccc125436a671e
   Main PID: 904 (python3)
      Tasks: 6 (limit: 373)
        CPU: 1min 45.143s
     CGroup: /system.slice/epaper-status.service
             └─904 /usr/bin/python3 /home/pitemplar/e-Paper/RaspberryPi_JetsonNano/python/PiTemplar/mem_display.py

Jan 23 22:35:35 PiTemplar systemd[1]: Started epaper-status.service - Waveshare ePaper System Status.
Jan 23 22:35:39 PiTemplar python3[904]: mem_display.py started (Pirata One title + SSID + disk usage)


No red error messages

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


###################### Now let's do SAMBA to make it work as a true file server now that the screen works!##############################

sudo apt update
sudo apt install -y samba samba-common-bin

once that install is done, do the smbclient

sudo apt update
sudo apt install -y smbclient

Verify: 

smbd --version

should see 
Version 4.22.6-Raspbian-4.22.6+dfsg-0+deb13u1+rpi1


create the share

sudo mkdir /srv/pitemplar
sudo mkdir /srv/pitemplar/shares/
sudo mkdir /srv/pitemplar/shares/private
sudo chmod 770 /srv/pitemplar/shares/private

sudo cp /etc/samba/smb.conf /etc/samba/smb.conf.bak  (maybe pull it to your drive via ftp)

Edit Samba config:

sudo nano /etc/samba/smb.conf

Replace everything below [global] with this:
[global]
   workgroup = WORKGROUP
   server string = PiTemplar NAS
   netbios name = PITEMPLAR
   security = USER
   map to guest = Never
   dns proxy = no
   log file = /var/log/samba/log.%m
   max log size = 1000
   load printers = no
   printcap name = /dev/null
   disable spoolss = yes

[private]
   path = /srv/pitemplar/shares/private
   browseable = yes
   writable = yes
   guest ok = no
   read only = no
   valid users = pitemplar


Save and exit

sudo nano /etc/samba/smb.conf


Create Samba user

Even though templar exists, Samba needs its own password.

sudo smbpasswd -a pitemplar
sudo smbpasswd -e pitemplar

Restart and enable Samba
sudo systemctl restart smbd
sudo systemctl enable smbd

systemctl status smbd

Test from another device
Windows
\\pitemplar\private

macOS / Linux
smb://templar/private


########################## Let's do web GUI, Experimental, but will allow us to switch networks easier.#################################
Here’s a step-by-step guide for your web GUI.

1️⃣ Create a systemd service file

sudo apt install -y python3-venv python3-full
sudo apt install python3-full -y

python3 -m venv venv
source venv/bin/activate

which python
# Should output something like ~/PiTemplar/venv/bin/python

pip install --upgrade pip
pip install flask psutil

Run:

sudo nano /etc/systemd/system/web_gui.service


Paste this:

[Unit]
Description=Raspberry Pi E-Paper Web GUI
After=network.target

[Service]
Type=simple
User=pitemplar
WorkingDirectory=/home/pitemplar/e-Paper/RaspberryPi_JetsonNano/python/PiTemplar
ExecStart=/home/pitemplar/e-Paper/RaspberryPi_JetsonNano/python/PiTemplar/venv/bin/python /home/pitemplar/e-Paper/RaspberryPi_JetsonNano/python/PiTemplar/web_gui.py
Restart=always
RestartSec=5
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target


sudo systemctl daemon-reload
sudo systemctl restart web_gui.service
sudo systemctl status web_gui.service


Important:
Restart at boot:
sudo systemctl enable web_gui.service

4️⃣ Start the service now
sudo systemctl start web_gui.service

5️⃣ Check status
sudo systemctl status web_gui.service


You should see something like:

Active: active (running) since ...

Login to verify, open a browser and type IP:8080




🎩 Thank You ♥
💖 Support Me
If you like my work and want to support me, plz consider

https://www.paypal.me/Modernknight101

or buy a copy or my sci-fi book, available on Amazon

https://a.co/d/hx5OLOO Gods Among Us: Alienthology

