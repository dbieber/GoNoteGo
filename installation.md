## Installation Instructions

These instructions assume you're starting from a clean install of Raspbian,
and that your Raspberry Pi is connected to an external monitor.
Once you are set up, an external monitor will no longer be necessary.

1.  Clone GoNoteGo

  ```bash
mkdir -p /home/pi/code/github/dbieber
cd /home/pi/code/github/dbieber
git clone https://github.com/dbieber/GoNoteGo.git
```

2.  Set up settings

  ```bash
cd /home/pi/code/github/dbieber/GoNoteGo
cp gonotego/settings/secure_settings_template.py gonotego/settings/secure_settings.py
nano gonotego/settings/secure_settings.py  # Configure your settings here.
```

It's OK to leave settings that you're not using at their default values.

3. Put Google service key on device

* `mkdir /home/pi/secrets`  # Run on Raspberry Pi.
* `scp path/to/google_credentials.json pi@192.168.0.106:/home/pi/secrets/`  # Run on primary.

Run `hostname -I` on the Raspberry Pi to determine the IP address to use in the scp command.

4. Install dependencies

  ```bash
sudo apt update
sudo apt upgrade
sudo apt install firefox-esr xvfb portaudio19-dev libatlas-base-dev redis-server espeak rustc python3-dev

cd /home/pi/code/github/dbieber/GoNoteGo
mkdir out
pip3 install virtualenv
/home/pi/.local/bin/virtualenv env -p python3
./env/bin/pip install grpcio -U --no-binary=grpcio
./env/bin/pip install -e .
```

5. Start on boot

  ```bash
sudo nano /etc/rc.local
```
  Add this line to rc.local:
  `/home/pi/code/github/dbieber/GoNoteGo/env/bin/supervisord -c /home/pi/code/github/dbieber/GoNoteGo/gonotego/supervisord.conf`

6. Install geckodriver to /usr/local/bin

  ```bash
cd
wget https://github.com/mozilla/geckodriver/releases/download/v0.23.0/geckodriver-v0.23.0-arm7hf.tar.gz
tar -xvf geckodriver-v0.23.0-arm7hf.tar.gz
rm geckodriver-v0.23.0-arm7hf.tar.gz
sudo mv geckodriver /usr/local/bin
```

7. Set up Internet

* Run `sudo nano /etc/wpa_supplicant/wpa_supplicant.conf`
* Follow the guide at https://www.raspberrypi.org/documentation/computers/configuration.html to set up your wpa_supplicant.conf file.

Setting up internet through the operating system's UI may also work.

8. Set up your audio

* Make sure audio is coming out of the desired output device at an acceptable volume.

9. Verify everything's working!

* Type a text note and press enter; it should appear in your notes.
* Press your hotkey and speak an audio note; it too should appear in your notes.
* Type ":ok" and press enter; you should hear the machine say "ok".
* If you're having any trouble getting set up, open a [new GitHub issue](https://github.com/dbieber/GoNoteGo/issues).
* That's it; you're good to go! Happy note-taking!
