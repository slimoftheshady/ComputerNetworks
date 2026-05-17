# config.py
# Configuration file for Mini Internet Protocol Stack Simulator

# ==========================
# IP Address Configuration
# ==========================
IP_HOST_A = "10.0.1.10"
IP_ROUTER_R1_IF1 = "10.0.1.1"
IP_ROUTER_R1_IF2 = "10.0.2.1"
IP_HOST_B = "10.0.2.20"

# ==========================
# MAC Address Configuration
# ==========================
MAC_HOST_A = "AA:AA:AA:AA:AA:AA"
MAC_ROUTER_R1_IF1 = "BB:BB:BB:BB:BB:BB"
MAC_ROUTER_R1_IF2 = "CC:CC:CC:CC:CC:CC"
MAC_HOST_B = "DD:DD:DD:DD:DD:DD"

# ==========================
# Layer 2 - MAC Table Placeholders
# Each device can learn MAC addresses dynamically
# Format: {IP: MAC}
# ==========================
MAC_TABLE_HOST_A = {}
MAC_TABLE_HOST_B = {}
MAC_TABLE_ROUTER_R1_IF1 = {}
MAC_TABLE_ROUTER_R1_IF2 = {}

# ==========================
# Routing Tables
# Each entry: destination_network : (next_hop_ip, outgoing_interface)
# ==========================
ROUTING_TABLE_HOST_A = {
    "10.0.1.0/24": (None, "eth0"),  # Directly connected network, no next hop
    "10.0.2.0/24": (IP_ROUTER_R1_IF1, "eth0")
}

ROUTING_TABLE_HOST_B = {
    "10.0.2.0/24": (None, "eth0"),  # Directly connected
    "10.0.1.0/24": (IP_ROUTER_R1_IF2, "eth0")
}

ROUTING_TABLE_ROUTER_R1 = {
    "10.0.1.0/24": (None, "if1"),  # Directly connected
    "10.0.2.0/24": (None, "if2")   # Directly connected
}

# ==========================
# Protocol Settings
# ==========================
ETH_TYPE_IPV4 = 0x0800
IP_PROTOCOL_UDP = 17
DEFAULT_TTL = 100

# ==========================
# Transport Layer Settings
# ==========================
MAX_SEGMENT_SIZE = 500  # Maximum application data per UDP-like segment

# Ports
PORT_A_TO_B = 5000
PORT_B_TO_A = 80

# ==========================
# Other Simulation Parameters
# ==========================
VERBOSE_LOGGING = True  # Print logs during simulation

