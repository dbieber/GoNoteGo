# Go Note Go Build Scripts

This directory contains scripts used in the build process for creating the Go Note Go Raspberry Pi image.

## Scripts

- `setup_wifi_ap.sh`: Sets up the WiFi access point for the Go Note Go device
- `setup_boot.sh`: Configures the system to start Go Note Go on boot and sets initial system settings
- `install_geckodriver.sh`: Installs the geckodriver needed for browser automation

These scripts are used by the GitHub workflow defined in `.github/workflows/build.yml`.
