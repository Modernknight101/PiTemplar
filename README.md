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

reboot python3 /home/bjorn/e-Paper/RaspberryPi_JetsonNano/python/mem_display.py 

⚠️ Important e-Paper Notes

Do NOT refresh too fast (≤30s is good)

Frequent refreshes shorten panel life

Waveshare e-paper is slow by design — that’s normal
