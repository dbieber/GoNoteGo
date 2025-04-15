#!/bin/bash
# Install geckodriver for browser automation

echo "Install geckodriver to known location"
cd
wget https://github.com/mozilla/geckodriver/releases/download/v0.23.0/geckodriver-v0.23.0-arm7hf.tar.gz
tar -xvf geckodriver-v0.23.0-arm7hf.tar.gz
rm geckodriver-v0.23.0-arm7hf.tar.gz
sudo mv geckodriver /usr/local/bin
