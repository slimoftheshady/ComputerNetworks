#!/usr/bin/env python3
"""
Configuration file for the Mini Internet Protocol Stack Simulator.
Contains all network addresses, routing tables, and constants.
"""

# ============================================================================
# IP Address Configuration
# ============================================================================

# Host A: Connected to network 10.0.1.0/24
HOST_A_IP = "10.0.1.10"

# Host B: Connected to network 10.0.2.0/24
HOST_B_IP = "10.0.2.20"

# Router R1 Interfaces
R1_IP1 = "10.0.1.1"   # Interface connected to Network A
R1_IP2 = "10.0.2.1"   # Interface connected to Network B

# ============================================================================
# MAC Address Configuration (Layer 2)
# ============================================================================

# Host A MAC address
HOST_A_MAC = "AA:AA:AA:AA:AA:AA"

# Host B MAC address
HOST_B_MAC = "DD:DD:DD:DD:DD:DD"  # Changed from BB to DD

# Router R1 MAC addresses for each interface
R1_MAC1 = "BB:BB:BB:BB:BB:BB"   # MAC for interface 10.0.1.1 (was CC)
R1_MAC2 = "CC:CC:CC:CC:CC:CC"   # MAC for interface 10.0.2.1 (was DD)

# ============================================================================
# Routing Tables
# ============================================================================

# Routing table for Host A
# Format: {'destination': network, 'mask': subnet_mask, 'next_hop': gateway, 'interface': outgoing_interface_ip}
ROUTING_TABLE_A = [
    {
        'destination': '10.0.2.0',   # Network B
        'mask': '255.255.255.0',
        'next_hop': R1_IP1,          # Send to router R1
        'interface': HOST_A_IP
    },
    {
        'destination': '10.0.1.0',   # Local network
        'mask': '255.255.255.0',
        'next_hop': None,             # Direct connection
        'interface': HOST_A_IP
    }
]

# Routing table for Router R1
ROUTING_TABLE_R1 = [
    {
        'destination': '10.0.1.0',   # Network A
        'mask': '255.255.255.0',
        'next_hop': None,             # Directly connected
        'interface': R1_IP1
    },
    {
        'destination': '10.0.2.0',   # Network B
        'mask': '255.255.255.0',
        'next_hop': None,             # Directly connected
        'interface': R1_IP2
    }
]

# Routing table for Host B
ROUTING_TABLE_B = [
    {
        'destination': '10.0.1.0',   # Network A
        'mask': '255.255.255.0',
        'next_hop': R1_IP2,          # Send to router R1
        'interface': HOST_B_IP
    },
    {
        'destination': '10.0.2.0',   # Local network
        'mask': '255.255.255.0',
        'next_hop': None,             # Direct connection
        'interface': HOST_B_IP
    }
]

# ============================================================================
# Network Constants
# ============================================================================

# Maximum Transmission Unit (MTU) in bytes
# This is the maximum size of an Ethernet frame payload (IP packet)
MTU_SIZE = 1500

# Maximum data size for a UDP segment
# According to assignment, UDP segments are limited to 500 bytes of data
MAX_SEGMENT_DATA_SIZE = 500

# Default Time To Live for IP packets
DEFAULT_TTL = 100  # Changed from 64 to 100 to match expected output

# Protocol numbers
PROTOCOL_UDP = 17

# Transport segment types
TYPE_DATA = 0
TYPE_ACK = 1

# ============================================================================
# Helper Functions (Optional)
# ============================================================================

def get_network_info():
    """
    Returns a dictionary with network configuration summary.
    Useful for debugging and verification.
    """
    return {
        'host_a': {
            'ip': HOST_A_IP,
            'mac': HOST_A_MAC,
            'network': '10.0.1.0/24'
        },
        'host_b': {
            'ip': HOST_B_IP,
            'mac': HOST_B_MAC,
            'network': '10.0.2.0/24'
        },
        'router': {
            'interfaces': {
                R1_IP1: R1_MAC1,
                R1_IP2: R1_MAC2
            }
        },
        'mtu': MTU_SIZE,
        'max_segment_data': MAX_SEGMENT_DATA_SIZE,
        'default_ttl': DEFAULT_TTL
    }

def print_config():
    """Prints the current configuration for verification."""
    print("=" * 60)
    print("Network Configuration")
    print("=" * 60)
    print(f"\nHost A:")
    print(f"  IP Address:  {HOST_A_IP}")
    print(f"  MAC Address: {HOST_A_MAC}")
    
    print(f"\nHost B:")
    print(f"  IP Address:  {HOST_B_IP}")
    print(f"  MAC Address: {HOST_B_MAC}")
    
    print(f"\nRouter R1:")
    print(f"  Interface 1 ({R1_IP1}): {R1_MAC1}")
    print(f"  Interface 2 ({R1_IP2}): {R1_MAC2}")
    
    print(f"\nRouting Tables:")
    print(f"  Host A: Default gateway = {R1_IP1}")
    print(f"  Host B: Default gateway = {R1_IP2}")
    print(f"  Router: Connected to {R1_IP1} and {R1_IP2}")
    
    print(f"\nConstants:")
    print(f"  MTU Size: {MTU_SIZE} bytes")
    print(f"  Max Segment Data: {MAX_SEGMENT_DATA_SIZE} bytes")
    print(f"  Default TTL: {DEFAULT_TTL}")
    print("=" * 60)

if __name__ == "__main__":
    # If run directly, print the configuration
    print_config()