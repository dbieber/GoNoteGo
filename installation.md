## Installation Instructions

1.  Clone GoNoteGo

  ```bash
mkdir -p /home/pi/code/github/dbieber
cd /home/pi/code/github/dbieber
git clone https://github.com/dbieber/GoNoteGo.git
```

2.  Set up settings

  ```bash
cd /home/pi/code/github/dbieber/GoNoteGo
cp gonotego/settings/secure_settings_template.py  gonotego/settings/secure_settings.py
nano gonotego/settings/secure_settings.py  
```
  * Configure your settings here.

3. Put google service key on device

  * mkdir /home/pi/secrets  # Run on Pi.
  * scp /Users/dbieber/david-bieber-4509b70e0c20.json pi@192.168.0.106:/home/pi/secrets/  # Run on primary.

4. Install dependencies

  * sudo apt update
  * sudo apt install iceweasel xvfb portaudio19-dev libatlas-base-dev redis-server espeak

  * cd /home/pi/code/github/dbieber/GoNoteGo
  * mkdir out
  * pip3 install virtualenv
  * /home/pi/.local/bin/virtualenv env -p python3
  * ./env/bin/pip install -r requirements.txt 

5. Start on boot

  * sudo nano /etc/rc.local
  * /home/pi/code/github/dbieber/GoNoteGo/env/bin/supervisord -c /home/pi/code/github/dbieber/GoNoteGo/gonotego/supervisord.conf  # Add this line to rc.local

6. Install geckodriver to /usr/local/bin

  * cd
  * wget https://github.com/mozilla/geckodriver/releases/download/v0.23.0/geckodriver-v0.23.0-arm7hf.tar.gz
  * tar -xvf geckodriver-v0.23.0-arm7hf.tar.gz
  * rm geckodriver-v0.23.0-arm7hf.tar.gz
  * sudo mv geckodriver /usr/local/bin

7. Set up Internet

  * Follow the guide at https://www.raspberrypi.org/documentation/computers/configuration.html to set your wpa_supplicant.
  * sudo nano /etc/wpa_supplicant/wpa_supplicant.conf

8. Set up your audio

  * Follow the guide at https://learn.adafruit.com/adafruit-voice-bonnet/raspberry-pi-setup if using an Adafruit Voice Bonnet.
