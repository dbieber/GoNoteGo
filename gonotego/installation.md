# Clone GoNoteGo
# Set up settings
# Put google service key on device
cd /home/pi/code/github/dbieber/GoNoteGo
pip3 install virtualenv
/home/pi/.local/bin/virtualenv env -p python3
./env/bin/pip install -r requirements.txt 

# sudo nano /etc/rc.local
/home/pi/code/github/dbieber/GoNoteGo/env/bin/supervisord -c /home/pi/code/github/dbieber/GoNoteGo/gonotego/supervisord.conf

sudo apt install iceweasel
sudo apt install xvfb
# Install geckodriver to /usr/local/bin

# Follow the guide at https://www.raspberrypi.org/documentation/computers/configuration.html to set your wpa_supplicant
# to configure your Raspberry Pi to connect to the internet.
# sudo nano /etc/wpa_supplicant/wpa_supplicant.conf
