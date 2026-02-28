set -e

echo "=== 1️⃣ Install Samba & smbclient ==="
sudo apt update
sudo apt install -y samba samba-common-bin smbclient

echo "=== 2️⃣ Create shared directories ==="
mkdir -p /srv/pitemplar/shares/private
chown -R pitemplar:pitemplar /srv/pitemplar/shares
chmod -R 770 /srv/pitemplar/shares

echo "=== 3️⃣ Backup and write Samba config ==="
cp /etc/samba/smb.conf /etc/samba/smb.conf.bak

cat <<EOL > /etc/samba/smb.conf
[global]
   workgroup = WORKGROUP
   server string = PiTemplar NAS
   netbios name = PITEMPLAR
   security = USER
   map to guest = Never
   dns proxy = no
   log file = /var/log/samba/log.%m
   max log size = 1000

[private]
   path = /srv/pitemplar/shares/private
   browseable = yes
   writable = yes
   guest ok = no
   read only = no
   valid users = pitemplar
EOL

echo "=== 4️⃣ Add Samba user ==="
echo "Please enter a Samba password for user 'pitemplar':"
smbpasswd -a pitemplar
smbpasswd -e pitemplar

echo "=== 5️⃣ Restart Samba and enable at boot ==="
systemctl restart smbd
systemctl enable smbd

echo "=== ✅ Setup complete! ==="
echo "Test locally with: smbclient -L localhost -U pitemplar"
echo "Access from Windows using: \\\\<Pi_IP>\\private"

