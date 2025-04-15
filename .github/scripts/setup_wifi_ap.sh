#!/bin/bash
# Setup WiFi Access Point for GoNoteGo

# Install required packages
sudo apt install -y rng-tools hostapd dnsmasq 

# Configure dhcpcd
cat <<EOF > /etc/dhcpcd.conf
# Allow users of this group to interact with dhcpcd via the control socket.
#controlgroup wheel

# Inform the DHCP server of our hostname for DDNS.
hostname

# Use the hardware address of the interface for the Client ID.
clientid
# or
# Use the same DUID + IAID as set in DHCPv6 for DHCPv4 ClientID as per RFC4361.
# Some non-RFC compliant DHCP servers do not reply with this set.
# In this case, comment out duid and enable clientid above.
#duid

# Persist interface configuration when dhcpcd exits.
persistent

# Rapid commit support.
# Safe to enable by default because it requires the equivalent option set
# on the server to actually work.
option rapid_commit

# A list of options to request from the DHCP server.
option domain_name_servers, domain_name, domain_search, host_name
option classless_static_routes
# Respect the network MTU. This is applied to DHCP routes.
option interface_mtu

# Most distributions have NTP support.
#option ntp_servers

# A ServerID is required by RFC2131.
require dhcp_server_identifier

# Generate SLAAC address using the Hardware Address of the interface
#slaac hwaddr
# OR generate Stable Private IPv6 Addresses based from the DUID
slaac private

# Example static IP configuration:
#interface eth0
#static ip_address=192.168.0.10/24
#static ip6_address=fd51:42f8:caae:d92e::ff/64
#static routers=192.168.0.1
#static domain_name_servers=192.168.0.1 8.8.8.8 fd51:42f8:caae:d92e::1

# It is possible to fall back to a static IP if DHCP fails:
# define static profile
#profile static_eth0
#static ip_address=192.168.1.23/24
#static routers=192.168.1.1
#static domain_name_servers=192.168.1.1

# fallback to static profile on eth0
#interface eth0
#fallback static_eth0

# Interface for Go Note Go Access Point
interface uap0
static ip_address=192.168.4.1/24
nohook wpa_supplicant
EOF

# Configure dnsmasq
cat <<EOF >> /etc/dnsmasq.conf
interface=uap0
dhcp-range=192.168.4.2,192.168.4.20,255.255.255.0,24h
EOF

# Create uap0 service
cat <<EOF >> /etc/systemd/system/uap0.service
[Unit]
Description=Create uap0 interface
After=sys-subsystem-net-devices-wlan0.device

[Service]
Type=oneshot
RemainAfterExit=true
ExecStart=/sbin/iw phy phy0 interface add uap0 type __ap
ExecStartPost=/usr/bin/ip link set dev uap0 address d8:3a:dd:06:5e:ca
ExecStartPost=/sbin/ifconfig uap0 up
ExecStop=/sbin/iw dev uap0 del

[Install]
WantedBy=multi-user.target
EOF

# Enable and start uap0 service
sudo systemctl daemon-reload
sudo systemctl start uap0.service
sudo systemctl enable uap0.service

# Configure hostapd
cat <<EOF >> /etc/hostapd/hostapd.conf
interface=uap0
ssid=GoNoteGo-Wifi
hw_mode=g
channel=4
wmm_enabled=0
macaddr_acl=0
auth_algs=1
ignore_broadcast_ssid=0
wpa=2
wpa_passphrase=swingset
wpa_key_mgmt=WPA-PSK
wpa_pairwise=TKIP
rsn_pairwise=CCMP
EOF

# Update hostapd defaults
cat <<EOF >> /etc/default/hostapd
DAEMON_CONF="/etc/hostapd/hostapd.conf"
EOF

# Start and enable hostapd and dnsmasq
sudo systemctl start hostapd
sudo systemctl start dnsmasq
sudo systemctl enable hostapd
sudo systemctl enable dnsmasq

# Enable IP forwarding
cat <<EOF >> /etc/sysctl.conf
net.ipv4.ip_forward=1
EOF