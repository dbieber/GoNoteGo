#!/bin/bash
# Configure system to start Go Note Go on boot

# Modify rc.local to start Go Note Go on boot
sudo cat /etc/rc.local
sudo sed '/^exit 0/i \
sudo -u pi mkdir -p /home/pi/out \
bash /home/pi/code/github/dbieber/GoNoteGo/scripts/install_settings.sh \
/home/pi/code/github/dbieber/GoNoteGo/env/bin/supervisord -c /home/pi/code/github/dbieber/GoNoteGo/gonotego/supervisord.conf \
    ' /etc/rc.local > ./rc.local.modified && sudo mv ./rc.local.modified /etc/rc.local
sudo chmod +x /etc/rc.local

# Configure initial system settings
# Attempt to not run config on first boot
sudo apt purge piwiz -y
sudo raspi-config nonint do_wifi_country US
# Configure US keyboard layout
sudo raspi-config nonint do_configure_keyboard us
touch /boot/ssh
echo "pi:$(echo 'raspberry' | openssl passwd -6 -stdin)" | sudo tee /boot/userconf > /dev/null

# Enable SSH
ssh-keygen -A &&
update-rc.d ssh enable
