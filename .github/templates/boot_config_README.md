# Configuring this Go Note Go

Edit `secure_settings.py` in this folder to set up this Go Note Go before
its first boot -- no monitor needed. This folder lives on the SD card's
boot partition, so you can edit it from any computer that can read the
card.

On boot, Go Note Go installs `secure_settings.py` as its settings and
renames it to `secure_settings.py.bak` (so stale settings aren't re-applied
forever). To change settings from the SD card again later, rename it back
to `secure_settings.py` and edit it.

The two things worth setting before gifting a device:

1. WiFi -- so it can get online right away:

   ```python
   WIFI_NETWORKS = [
       {'ssid': 'YourNetworkName', 'psk': 'your-wifi-password'},
       {'ssid': 'SomeOpenNetwork'},  # no psk for open networks
   ]
   ```

2. Where notes go -- e.g. for email:

   ```python
   NOTE_TAKING_SYSTEM = 'email'
   EMAIL = 'recipient@example.com'
   EMAIL_USER = 'sender@gmail.com'
   EMAIL_PASSWORD = 'app-password'
   EMAIL_SERVER = 'smtp.gmail.com'
   ```

Anything left as a `<PLACEHOLDER>` is simply unconfigured; that's fine.

No SD card access? If the device can't find a WiFi network it knows, it
starts a setup hotspot (network `GoNoteGo-Wifi`, password `swingset`) and
speaks instructions; all of these settings can then be entered at
http://192.168.4.1:8000 from a phone.
