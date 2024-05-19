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
fi
