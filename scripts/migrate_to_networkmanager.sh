#!/bin/bash
# Script to assist in migrating from wpa_supplicant to NetworkManager

# Ensure the script is run with root privileges
if [ "$EUID" -ne 0 ]; then
  echo "Please run as root"
  exit 1
fi

echo "Migrating from wpa_supplicant to NetworkManager"

# Install NetworkManager if not already installed
echo "Installing NetworkManager..."
apt-get update
apt-get install -y network-manager

# Disable wpa_supplicant services
echo "Disabling wpa_supplicant services..."
systemctl mask wpa_supplicant.service
systemctl stop wpa_supplicant.service

# Enable NetworkManager
echo "Enabling NetworkManager..."
systemctl enable NetworkManager.service
systemctl start NetworkManager.service

# Migrate networks (this will be handled by GoNoteGo when you run the 'wifi-migrate' command)
echo "Run GoNoteGo and use the 'wifi-migrate' command to migrate your networks."
echo "Migration complete. Please reboot your system to complete the process."