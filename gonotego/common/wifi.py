"""WiFi utilities for Go Note Go.

This module provides functions for configuring WiFi networks.
"""
import os
import subprocess

def add_wpa_network(ssid, psk):
    """Add a WPA-secured WiFi network to wpa_supplicant.conf.
    
    Args:
        ssid: The network SSID (name)
        psk: The network password/passphrase
        
    Returns:
        bool: True if successful, False otherwise
    """
    if '"' in ssid or '"' in psk:
        return False
    
    network_string = f"""
network={{
        ssid="{ssid}"
        psk="{psk}"
        key_mgmt=WPA-PSK
}}
"""
    filepath = '/etc/wpa_supplicant/wpa_supplicant.conf'
    try:
        with open('/tmp/network_addition', 'w') as f:
            f.write(network_string)
        
        subprocess.run(
            f"sudo tee -a {filepath} < /tmp/network_addition",
            shell=True, check=True
        )
        os.remove('/tmp/network_addition')
        return True
    except Exception as e:
        print(f"Error adding WPA network: {e}")
        return False

def add_open_network(ssid):
    """Add an open (no password) WiFi network to wpa_supplicant.conf.
    
    Args:
        ssid: The network SSID (name)
        
    Returns:
        bool: True if successful, False otherwise
    """
    if '"' in ssid:
        return False
    
    network_string = f"""
network={{
        ssid="{ssid}"
        key_mgmt=NONE
}}
"""
    filepath = '/etc/wpa_supplicant/wpa_supplicant.conf'
    try:
        with open('/tmp/network_addition', 'w') as f:
            f.write(network_string)
        
        subprocess.run(
            f"sudo tee -a {filepath} < /tmp/network_addition",
            shell=True, check=True
        )
        os.remove('/tmp/network_addition')
        return True
    except Exception as e:
        print(f"Error adding open network: {e}")
        return False

def reconfigure_wifi():
    """Apply WiFi configuration changes.
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        subprocess.run('wpa_cli -i wlan0 reconfigure', shell=True, check=True)
        return True
    except Exception as e:
        print(f"Error reconfiguring WiFi: {e}")
        return False

def clear_networks():
    """Clear all WiFi networks from wpa_supplicant.conf.
    
    Keeps the country and ctrl_interface settings but removes all networks.
    
    Returns:
        bool: True if successful, False otherwise
    """
    filepath = '/etc/wpa_supplicant/wpa_supplicant.conf'
    try:
        # Read existing configuration
        with open(filepath, 'r') as f:
            lines = f.readlines()
        
        # Keep header settings but remove network blocks
        header_lines = []
        in_network_block = False
        for line in lines:
            if 'network=' in line:
                in_network_block = True
                continue
            if in_network_block:
                if '}' in line:
                    in_network_block = False
                continue
            header_lines.append(line)
        
        # Write back the header settings
        new_config = ''.join(header_lines)
        with open('/tmp/wpa_config', 'w') as f:
            f.write(new_config)
        
        subprocess.run(
            f"sudo cp /tmp/wpa_config {filepath}",
            shell=True, check=True
        )
        os.remove('/tmp/wpa_config')
        return True
    except Exception as e:
        print(f"Error clearing networks: {e}")
        return False

def configure_from_settings(networks):
    """Configure WiFi networks from settings.
    
    Args:
        networks: List of network dictionaries with 'ssid' and 'psk' keys
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Clear existing networks
        if not clear_networks():
            return False
        
        # Add each network from settings
        for network in networks:
            if not network.get('ssid'):
                continue
                
            if network.get('psk'):
                # WPA network
                add_wpa_network(network['ssid'], network['psk'])
            else:
                # Open network
                add_open_network(network['ssid'])
        
        # Apply changes
        return reconfigure_wifi()
    except Exception as e:
        print(f"Error configuring WiFi from settings: {e}")
        return False