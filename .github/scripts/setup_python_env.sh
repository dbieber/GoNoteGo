#!/bin/bash
# Setup Python environment for GoNoteGo

echo "Setting up Python environment"
python3 -m venv env
./env/bin/pip install -e .  # Install Python dependencies

echo "Setting up Go Note Go:"
cp gonotego/settings/secure_settings_template.py gonotego/settings/secure_settings.py
echo "Manually edit secure_settings.py to configure your settings."

mkdir -p /home/pi/secrets
echo "Manually transfer secrets to /home/pi/secrets."

# Ensure repository is owned by pi user instead of root
chown -R pi:pi /home/pi/code/github/dbieber/GoNoteGo