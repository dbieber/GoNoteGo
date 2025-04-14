"""WiFi settings module for Go Note Go using NetworkManager."""
import json
import subprocess
import re
from gonotego.settings import settings
from gonotego.command_center import system_commands

shell = system_commands.shell


def get_networks():
    """Get the list of WiFi networks from Redis settings."""
    try:
        return json.loads(settings.get('WIFI_NETWORKS') or '[]')
    except (json.JSONDecodeError, TypeError):
        return []


def save_networks(networks):
    """Save the list of WiFi networks to Redis settings."""
    settings.set('WIFI_NETWORKS', json.dumps(networks))


def update_network_connections():
    """Update NetworkManager connections for Go Note Go managed WiFi networks."""
    networks = get_networks()
    result = True
    
    try:
        # Get existing connections managed by Go Note Go
        existing_connections = get_gonote_managed_connections()
        
        # Remove connections no longer in our networks list
        managed_ssids = [network['ssid'] for network in networks]
        for conn_name in existing_connections:
            if conn_name not in managed_ssids:
                remove_connection(conn_name)
        
        # Add or update each network
        for network in networks:
            ssid = network['ssid']
            
            # Check if connection already exists
            if ssid in existing_connections:
                # Remove and recreate with new settings
                remove_connection(ssid)
            
            # Create new connection
            if network.get('psk'):
                # WPA secured network
                add_wpa_connection(ssid, network['psk'])
            else:
                # Open network
                add_open_connection(ssid)
        
        return result
    except Exception as e:
        print(f"Error updating NetworkManager connections: {e}")
        return False


def get_gonote_managed_connections():
    """Get list of WiFi connections currently managed by Go Note Go."""
    try:
        result = subprocess.run(
            ["nmcli", "-t", "-f", "NAME,TYPE", "connection", "show"],
            capture_output=True, text=True, check=True
        )
        
        # Filter connections that are wifi and have names matching our managed networks
        connections = []
        networks = get_networks()
        managed_ssids = [network['ssid'] for network in networks]
        
        for line in result.stdout.splitlines():
            parts = line.split(':', 1)
            if len(parts) == 2:
                name, conn_type = parts
                if conn_type == 'wifi' and name in managed_ssids:
                    connections.append(name)
        
        return connections
    except subprocess.CalledProcessError as e:
        print(f"Error getting NetworkManager connections: {e}")
        return []


def add_wpa_connection(ssid, password):
    """Add a new WPA secured WiFi connection."""
    try:
        conn_name = ssid
        
        cmd = [
            "sudo", "nmcli", "connection", "add",
            "type", "wifi",
            "con-name", conn_name,
            "ifname", "wlan0",
            "ssid", ssid,
            "wifi-sec.key-mgmt", "wpa-psk",
            "wifi-sec.psk", password
        ]
        
        subprocess.run(cmd, check=True, capture_output=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error adding WPA connection for {ssid}: {e}")
        print(f"Error output: {e.stderr}")
        return False


def add_open_connection(ssid):
    """Add a new open (unsecured) WiFi connection."""
    try:
        conn_name = ssid
        
        cmd = [
            "sudo", "nmcli", "connection", "add",
            "type", "wifi",
            "con-name", conn_name,
            "ifname", "wlan0",
            "ssid", ssid
        ]
        
        subprocess.run(cmd, check=True, capture_output=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error adding open connection for {ssid}: {e}")
        print(f"Error output: {e.stderr}")
        return False


def remove_connection(conn_name):
    """Remove a NetworkManager connection."""
    try:
        subprocess.run(
            ["sudo", "nmcli", "connection", "delete", conn_name],
            check=True, capture_output=True
        )
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error removing connection {conn_name}: {e}")
        print(f"Error output: {e.stderr}")
        return False


def reconfigure_wifi():
    """Reconnect to available WiFi networks."""
    # Refresh all connections and activate the best available one
    try:
        # Restart NetworkManager service to apply changes
        shell('sudo systemctl restart NetworkManager')
        
        # Get list of available configured networks
        networks = get_networks()
        
        # Try to connect to the first available network
        for network in networks:
            ssid = network['ssid']
            try:
                # Check if we can see this network
                result = subprocess.run(
                    ["nmcli", "-t", "-f", "SSID", "device", "wifi", "list"],
                    capture_output=True, text=True, check=True
                )
                
                available_networks = [line.strip() for line in result.stdout.splitlines()]
                
                if ssid in available_networks:
                    # Try to connect to this network
                    subprocess.run(
                        ["nmcli", "connection", "up", "id", ssid],
                        check=True, capture_output=True
                    )
                    print(f"Connected to {ssid}")
                    break
            except Exception as e:
                print(f"Error connecting to {ssid}: {e}")
                continue
        
        return True
    except Exception as e:
        print(f"Error reconfiguring WiFi: {e}")
        return False


def migrate_networks_from_wpa_supplicant():
    """Scan wpa_supplicant.conf and migrate existing networks to Redis."""
    filepath = '/etc/wpa_supplicant/wpa_supplicant.conf'
    
    if not subprocess.run(["test", "-f", filepath], capture_output=True).returncode == 0:
        print('WiFi configuration file not found.')
        return None
    
    try:
        # Read the existing configuration
        with open(filepath, 'r') as f:
            config = f.read()
        
        # Extract network blocks
        network_blocks = re.findall(r'network\s*=\s*{(.*?)}', config, re.DOTALL)
        
        # Process each network block
        networks = []
        for block in network_blocks:
            # Extract SSID
            ssid_match = re.search(r'ssid\s*=\s*"(.*?)"', block)
            if not ssid_match:
                continue
            
            ssid = ssid_match.group(1)
            
            # Check if it's an open network
            if 'key_mgmt=NONE' in block:
                networks.append({'ssid': ssid})
            else:
                # Extract password for WPA networks
                psk_match = re.search(r'psk\s*=\s*"(.*?)"', block)
                if psk_match:
                    psk = psk_match.group(1)
                    networks.append({'ssid': ssid, 'psk': psk})
        
        return networks
    except Exception as e:
        print(f"Error migrating WiFi networks: {e}")
        return None


def migrate_from_networkmanger():
    """Scan NetworkManager connections and migrate to Redis."""
    try:
        # Get all wifi connections
        result = subprocess.run(
            ["nmcli", "-t", "-f", "NAME,TYPE", "connection", "show"],
            capture_output=True, text=True, check=True
        )
        
        wifi_connections = []
        for line in result.stdout.splitlines():
            parts = line.split(':', 1)
            if len(parts) == 2:
                name, conn_type = parts
                if conn_type == 'wifi':
                    wifi_connections.append(name)
        
        networks = []
        for conn_name in wifi_connections:
            # Get connection details
            result = subprocess.run(
                ["sudo", "nmcli", "--show-secrets", "connection", "show", conn_name],
                capture_output=True, text=True, check=True
            )
            
            # Parse output to get SSID and PSK
            ssid = None
            psk = None
            
            for line in result.stdout.splitlines():
                if "802-11-wireless.ssid:" in line:
                    ssid = line.split(":", 1)[1].strip()
                elif "802-11-wireless-security.psk:" in line:
                    psk = line.split(":", 1)[1].strip()
            
            if ssid:
                if psk:
                    networks.append({'ssid': ssid, 'psk': psk})
                else:
                    networks.append({'ssid': ssid})
        
        return networks
    except Exception as e:
        print(f"Error migrating from NetworkManager: {e}")
        return None
