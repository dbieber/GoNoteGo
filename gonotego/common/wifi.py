"""WiFi management utilities.

This module provides functions to manage WiFi connections, including listing available
networks, connecting to networks, and retrieving current connection status.
"""
import subprocess
import re
import time
import os
from gonotego.settings import settings

def get_wifi_status():
    """Get the current WiFi connection status.
    
    Returns:
        dict: A dictionary containing WiFi status information including:
              - connected (bool): Whether we're connected to WiFi
              - ssid (str): The SSID of the connected network, if any
              - signal_strength (str): Signal strength as a percentage, if connected
              - ip_address (str): The IP address assigned to the WiFi interface, if connected
    """
    status = {
        'connected': False,
        'ssid': None,
        'signal_strength': None,
        'ip_address': None
    }
    
    try:
        # Use iwconfig to check WiFi status
        output = subprocess.check_output(['iwconfig', 'wlan0'], stderr=subprocess.STDOUT).decode('utf-8')
        
        # Check if connected to an ESSID
        ssid_match = re.search(r'ESSID:"([^"]*)"', output)
        if ssid_match and ssid_match.group(1) != "off/any":
            status['connected'] = True
            status['ssid'] = ssid_match.group(1)
            
            # Get signal strength
            signal_match = re.search(r'Signal level=([0-9-]+)', output)
            if signal_match:
                # Convert dBm to percentage (rough estimation)
                dbm = int(signal_match.group(1))
                if dbm <= -100:
                    percentage = 0
                elif dbm >= -50:
                    percentage = 100
                else:
                    percentage = 2 * (dbm + 100)
                status['signal_strength'] = f"{percentage}%"
            
            # Get IP address
            try:
                ip_output = subprocess.check_output(['hostname', '-I']).decode('utf-8').strip()
                if ip_output:
                    status['ip_address'] = ip_output.split()[0]  # First IP is usually WiFi
            except subprocess.CalledProcessError:
                pass
    except (subprocess.CalledProcessError, FileNotFoundError, IndexError) as e:
        # Log the error but return empty status
        print(f"Error getting WiFi status: {e}")
    
    return status

def scan_networks():
    """Scan for available WiFi networks.
    
    Returns:
        list: A list of dictionaries, each containing information about an available network:
              - ssid (str): The network name
              - signal_strength (str): Signal strength as a percentage
              - encryption (str): The encryption type (WPA, WEP, Open)
    """
    networks = []
    
    try:
        # Use iwlist to scan for networks
        output = subprocess.check_output(['sudo', 'iwlist', 'wlan0', 'scan']).decode('utf-8')
        
        # Parse the output to extract networks
        cells = output.split('Cell ')
        for cell in cells[1:]:  # Skip the first element which is header
            ssid_match = re.search(r'ESSID:"([^"]*)"', cell)
            signal_match = re.search(r'Quality=([0-9]+)/([0-9]+)', cell)
            encryption_match = re.search(r'Encryption key:(on|off)', cell)
            
            if ssid_match:
                network = {
                    'ssid': ssid_match.group(1),
                    'signal_strength': None,
                    'encryption': 'Unknown'
                }
                
                # Parse signal strength
                if signal_match:
                    quality = int(signal_match.group(1))
                    max_quality = int(signal_match.group(2))
                    percentage = int((quality / max_quality) * 100)
                    network['signal_strength'] = f"{percentage}%"
                
                # Parse encryption
                if encryption_match:
                    if encryption_match.group(1) == 'on':
                        if 'WPA' in cell:
                            network['encryption'] = 'WPA'
                        else:
                            network['encryption'] = 'WEP'
                    else:
                        network['encryption'] = 'Open'
                
                networks.append(network)
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        print(f"Error scanning WiFi networks: {e}")
    
    return networks

def connect_to_wifi(ssid, password):
    """Connect to a WiFi network.
    
    Args:
        ssid (str): The name of the network to connect to
        password (str): The password for the network
        
    Returns:
        bool: True if the connection was successful, False otherwise
    """
    try:
        # Create a wpa_supplicant configuration
        wpa_config = f'''
network={{
    ssid="{ssid}"
    psk="{password}"
}}
'''
        # Write the configuration to a temporary file
        with open('/tmp/wpa_supplicant.conf', 'w') as f:
            f.write(wpa_config)
        
        # Apply the configuration
        subprocess.check_call(['sudo', 'cp', '/tmp/wpa_supplicant.conf', '/etc/wpa_supplicant/wpa_supplicant.conf'])
        
        # Restart networking
        subprocess.check_call(['sudo', 'systemctl', 'restart', 'wpa_supplicant'])
        subprocess.check_call(['sudo', 'systemctl', 'restart', 'networking'])
        
        # Wait for the connection to establish
        time.sleep(5)
        
        # Check if connection was successful
        status = get_wifi_status()
        return status['connected'] and status['ssid'] == ssid
    except Exception as e:
        print(f"Error connecting to WiFi: {e}")
        return False

def apply_wifi_settings():
    """Apply WiFi settings from the settings module.
    
    This function retrieves the WIFI_SSID and WIFI_PASSWORD from settings
    and attempts to connect to the specified network.
    
    Returns:
        bool: True if the connection was successful, False otherwise
    """
    try:
        ssid = settings.get('WIFI_SSID')
        password = settings.get('WIFI_PASSWORD')
        
        if not ssid:
            print("No WiFi SSID configured in settings")
            return False
        
        return connect_to_wifi(ssid, password)
    except Exception as e:
        print(f"Error applying WiFi settings: {e}")
        return False