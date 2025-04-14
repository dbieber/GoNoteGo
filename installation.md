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

4. Start the settings server.
   
   Type the following command and press Enter:
   ```
   :server
   ```
   
   This will start a WiFi hotspot called GoNoteGo-Wifi.

5. Connect to the GoNoteGo-Wifi hotspot.
   
   Connect from another device like a phone or computer.
   The password is: `swingset`.

6. Configure your Go Note Go.
   
   Navigate to: `192.168.4.1:8000`.
   
   Here you can configure:
   - WiFi networks to connect to
   - Where to upload your notes
   - Other settings
   
   Click Save when finished.

7. Verify internet connection.
   
   Run the following command on the Go Note Go:
   ```
   :i
   ```
   
   It should respond out loud with 'Yes' indicating it's connected to the internet.

8. Turn off the WiFi hotspot (optional).
   
   Run the following command:
   ```
   :server stop
   ```

9. That's it! Your Go Note Go is ready to use. Happy note-taking!

If you're having any trouble getting set up, open a [new GitHub issue](https://github.com/dbieber/GoNoteGo/issues).