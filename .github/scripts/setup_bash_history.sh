#!/bin/bash
# Add useful commands to the bash history for debugging purposes

cat << EOF >> /home/pi/.bash_history
sudo reboot now
sudo systemctl daemon-reload
sudo systemctl status uap0.service
sudo systemctl status dnsmasq.service
sudo systemctl status hostapd.service
sudo journalctl -u uap0.service
sudo journalctl -u dnsmasq.service
sudo journalctl -u hostapd.service
ip addr show uap0
sudo ip addr add 192.168.4.1/24 dev uap0
cat /etc/rc.local
cat /etc/default/hostapd
cat /etc/hostapd/hostapd.conf
cat /etc/systemd/system/uap0.service
cat /etc/sysctl.conf
cat /etc/dhcpcd.conf
cat /etc/dnsmasq.conf
python -m http.server
sudo iptables -t nat -A POSTROUTING -o wlan0 -j MASQUERADE
sudo iptables -t nat -L
sudo cat /etc/wpa_supplicant/wpa_supplicant.conf
sudo nano /etc/wpa_supplicant/wpa_supplicant.conf
nano /home/pi/code/github/dbieber/GoNoteGo/gonotego/settings/secure_settings.py
/home/pi/code/github/dbieber/GoNoteGo/env/bin/python
/home/pi/code/github/dbieber/GoNoteGo/env/bin/supervisord -c /home/pi/code/github/dbieber/GoNoteGo/gonotego/supervisord.conf
/home/pi/code/github/dbieber/GoNoteGo/env/bin/supervisorctl -u go -p notego status
/home/pi/code/github/dbieber/GoNoteGo/env/bin/supervisorctl -u go -p notego restart all
cd /home/pi/code/github/dbieber/GoNoteGo/
EOF