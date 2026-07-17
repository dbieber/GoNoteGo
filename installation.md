## Installation Instructions

These instructions will guide you through setting up Go Note Go on a Raspberry Pi 400.

1. Download the latest image from GitHub Actions artifacts.

2. Flash the image onto an SD card.
   
   Example commands (macOS):
   ```bash
   diskutil unmountDisk /dev/disk4
   sudo dd bs=4M if=/Users/yourusername/Downloads/go-note-go.img of=/dev/rdisk4 conv=fsync status=progress
   ```

3. Insert the SD card into the Raspberry Pi 400 and power it on.
   
   Give it a minute to boot.

4. Wait for the setup hotspot (or start it yourself).

   If Go Note Go can't find a WiFi network it knows, it automatically starts
   a hotspot called GoNoteGo-Wifi after about two minutes and speaks the
   network name, password, and settings address out loud.

   You can also start it any time by typing:
   ```
   :hotspot
   ```

5. Connect to the GoNoteGo-Wifi hotspot.
   
   Connect from another device like a phone or computer.
   The password is: `swingset`.

6. Configure your Go Note Go.
   
   Navigate to: `192.168.4.1:8000`.
   
   Here you can configure:
   - WiFi networks to connect to
   - Where to upload your notes
   - Other settings
   
   Settings save automatically as you edit (watch the saved/unsaved
   indicator in the corner).

7. Verify the WiFi connection.

   After adding a WiFi network, press its "Test connection" button. Go Note
   Go connects to the network while the hotspot stays up, verifies real
   internet access, and reports the result on the page and out loud. You can
   also ask the device directly:
   ```
   :i
   ```
   
   It should respond out loud with 'Yes' indicating it's connected to the internet.

8. Turn off the WiFi hotspot.

   Once a connection is verified, press "Turn off hotspot" on the settings
   page (it refuses until a connection has been verified, so you can't lock
   yourself out), or type:
   ```
   :hotspot off
   ```

9. That's it! Your Go Note Go is ready to use. Happy note-taking!

If you're having any trouble getting set up, open a [new GitHub issue](https://github.com/dbieber/GoNoteGo/issues).