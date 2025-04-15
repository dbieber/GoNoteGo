#!/bin/bash
# Setup WiFi Access Point for GoNoteGo

# Install required packages
sudo apt install -y rng-tools hostapd dnsmasq 

# Configure dhcpcd
sudo cp /home/pi/code/github/dbieber/GoNoteGo/.github/templates/dhcpcd.conf /etc/dhcpcd.conf

# Configure dnsmasq
sudo cp /home/pi/code/github/dbieber/GoNoteGo/.github/templates/dnsmasq.conf /etc/dnsmasq.conf

# Create uap0 service
sudo cp /home/pi/code/github/dbieber/GoNoteGo/.github/templates/uap0.service /etc/systemd/system/uap0.service

# Enable and start uap0 service
sudo systemctl daemon-reload
sudo systemctl start uap0.service
sudo systemctl enable uap0.service

# Configure hostapd
sudo cp /home/pi/code/github/dbieber/GoNoteGo/.github/templates/hostapd.conf /etc/hostapd/hostapd.conf

# Update hostapd defaults
sudo cp /home/pi/code/github/dbieber/GoNoteGo/.github/templates/hostapd /etc/default/hostapd

# Start and enable hostapd and dnsmasq
sudo systemctl start hostapd
sudo systemctl start dnsmasq
sudo systemctl enable hostapd
sudo systemctl enable dnsmasq

# Enable IP forwarding
sudo cp /home/pi/code/github/dbieber/GoNoteGo/.github/templates/sysctl.conf /etc/sysctl.conf