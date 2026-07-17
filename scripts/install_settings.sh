#!/bin/bash
# Runs at every boot (from rc.local), before Go Note Go's services start.
#
# If a secure_settings.py exists in the boot partition's gonotego/ folder,
# install it as the device's settings. The boot partition is FAT, so it can
# be edited from any computer with the SD card -- this is how a generic
# Go Note Go image is customized per recipient without ever attaching a
# monitor. After installing, the file is renamed to .bak so stale settings
# aren't re-applied on every boot (rename it back to re-apply).

target_dir="/home/pi/code/github/dbieber/GoNoteGo/gonotego/settings/"

# The boot partition mounts at /boot/firmware on Bookworm and /boot on
# older images.
for boot_dir in /boot/firmware /boot; do
    source_file="$boot_dir/gonotego/secure_settings.py"
    if [ -f "$source_file" ]; then
        cp "$source_file" "$target_dir"
        mv "$source_file" "$source_file.bak"
        break
    fi
done
