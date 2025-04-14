"""WiFi command handlers for Go Note Go using NetworkManager."""
from gonotego.command_center import registry
from gonotego.command_center import system_commands
from gonotego.settings import wifi

register_command = registry.register_command
say = system_commands.say
shell = system_commands.shell


@register_command('wifi {} {}')
@register_command('wpa {} {}')
def add_wpa_wifi(ssid, psk):
    if '"' in ssid or '"' in psk:
        say('WiFi not set.')
        return

    # Load existing networks
    networks = wifi.get_networks()

    # Check if this network already exists
    for network in networks:
        if network.get('ssid') == ssid:
            network['psk'] = psk
            break
    else:
        # Network doesn't exist, add it
        networks.append({'ssid': ssid, 'psk': psk})

    # Save updated networks
    wifi.save_networks(networks)
    
    # Update NetworkManager connections
    if wifi.update_network_connections():
        wifi.reconfigure_wifi()
        say(f'WiFi network {ssid} added.')
    else:
        say('Failed to update WiFi configuration.')


@register_command('wifi {}')
def add_wifi_no_psk(ssid):
    if '"' in ssid:
        say('WiFi not set.')
        return
    
    # Load existing networks
    networks = wifi.get_networks()
    
    # Check if this network already exists
    for network in networks:
        if network.get('ssid') == ssid:
            network.pop('psk', None)  # Remove password if it exists
            break
    else:
        # Network doesn't exist, add it
        networks.append({'ssid': ssid})
    
    # Save updated networks
    wifi.save_networks(networks)
    
    # Update NetworkManager connections
    if wifi.update_network_connections():
        wifi.reconfigure_wifi()
        say(f'Open WiFi network {ssid} added.')
    else:
        say('Failed to update WiFi configuration.')


@register_command('wifi-list')
def list_wifi_networks():
    networks = wifi.get_networks()
    if not networks:
        say('No WiFi networks configured.')
        return
    
    network_list = [f"{i+1}. {network['ssid']}" for i, network in enumerate(networks)]
    say('Configured WiFi networks: ' + ', '.join(network_list))


@register_command('wifi-migrate')
def migrate_wifi_networks():
    """Migrate existing networks from wpa_supplicant.conf to NetworkManager."""
    networks = wifi.migrate_networks_from_wpa_supplicant()
    
    if networks is None:
        say('WiFi configuration file not found or error reading it.')
        return
        
    # Save the extracted networks to Redis
    if networks:
        wifi.save_networks(networks)
        say(f'Migrated {len(networks)} WiFi networks to settings.')
        
        # Update NetworkManager connections
        wifi.update_network_connections()
        wifi.reconfigure_wifi()
    else:
        say('No WiFi networks found to migrate.')


@register_command('wifi-nm-migrate')
def migrate_from_networkmanager():
    """Migrate existing NetworkManager connections to Go Note Go settings."""
    networks = wifi.migrate_from_networkmanger()
    
    if networks is None:
        say('Error reading NetworkManager connections.')
        return
        
    # Save the extracted networks to Redis
    if networks:
        wifi.save_networks(networks)
        say(f'Migrated {len(networks)} WiFi networks from NetworkManager to settings.')
    else:
        say('No WiFi networks found to migrate.')


@register_command('wifi-remove {}')
def remove_wifi_network(ssid):
    networks = wifi.get_networks()
    initial_count = len(networks)
    
    # Remove networks with matching SSID
    networks = [network for network in networks if network.get('ssid') != ssid]
    
    if len(networks) < initial_count:
        # Save updated networks
        wifi.save_networks(networks)
        
        # Update NetworkManager connections
        if wifi.update_network_connections():
            wifi.reconfigure_wifi()
            say(f'WiFi network {ssid} removed.')
        else:
            say('Failed to update WiFi configuration.')
    else:
        say(f'WiFi network {ssid} not found.')


@register_command('reconnect')
@register_command('wifi-refresh')
@register_command('wifi-reconfigure')
def reconfigure_wifi():
    wifi.reconfigure_wifi()


@register_command('wifi-scan')
def scan_wifi_networks():
    """Scan for available WiFi networks."""
    try:
        # Ensure the WiFi adapter is on
        shell('sudo nmcli radio wifi on')
        
        # Scan for networks
        result = shell('nmcli -t -f SSID,SIGNAL,SECURITY device wifi list')
        
        networks = []
        for line in result.stdout.strip().split('\n'):
            if line:
                parts = line.split(':', 2)
                if len(parts) >= 3 and parts[0]:  # Ensure SSID is not empty
                    ssid, signal, security = parts
                    networks.append((ssid, int(signal), security))
        
        # Sort by signal strength (descending)
        networks.sort(key=lambda x: x[1], reverse=True)
        
        # Take the top 5 networks
        top_networks = networks[:5]
        
        if top_networks:
            network_list = [f"{i+1}. {ssid} ({signal}%)" 
                           for i, (ssid, signal, _) in enumerate(top_networks)]
            say('Available WiFi networks: ' + ', '.join(network_list))
        else:
            say('No WiFi networks found.')
    except Exception as e:
        say(f'Error scanning for WiFi networks: {str(e)}')
