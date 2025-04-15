# GoNoteGo Build Scripts

This directory contains scripts used in the build process for creating the GoNoteGo Raspberry Pi image.

## Scripts

- `setup_wifi_ap.sh`: Sets up the WiFi access point for the GoNoteGo device
- `setup_boot.sh`: Configures the system to start GoNoteGo on boot and sets initial system settings
- `setup_python_env.sh`: Sets up the Python environment for GoNoteGo
- `install_geckodriver.sh`: Installs the geckodriver needed for browser automation
- `setup_bash_history.sh`: Sets up useful commands in bash history for debugging purposes

These scripts are used by the GitHub workflow defined in `.github/workflows/build.yml`.