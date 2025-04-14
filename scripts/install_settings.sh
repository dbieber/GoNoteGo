#!/bin/bash

# Define the source and target file paths
source_file="/boot/firmware/gonotego/secure_settings.py"
target_dir="/home/pi/code/github/dbieber/GoNoteGo/gonotego/settings/"
backup_file="/boot/firmware/gonotego/secure_settings.py.bak"

# Check if the source file exists
if [ -f "$source_file" ]; then
    # Copy the file to the target directory
    cp "$source_file" "$target_dir"

    # Rename the original file to a backup file
    mv "$source_file" "$backup_file"
    
    # Ensure the copied settings file is owned by pi user
    chown pi:pi "$target_dir/$(basename "$source_file")"
fi

# Ensure the entire GoNoteGo repo is owned by pi user
chown -R pi:pi /home/pi/code/github/dbieber/GoNoteGo
