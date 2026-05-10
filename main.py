#!/usr/bin/env python3
import sys
import os

# Makes sure network package can be imported
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from network.protocol import Frame, IPPacket, Segment
from network.devices import Host, Router
from network.config import (
    # IP Addresses
    HOST_A_IP,
    HOST_B_IP,
    R1_IP1,
    R1_IP2,
    
    # MAC Addresses
    HOST_A_MAC,
    HOST_B_MAC,
    R1_MAC1,
    R1_MAC2,
    
    # Routing Tables
    ROUTING_TABLE_A,
    ROUTING_TABLE_B,
    ROUTING_TABLE_R1,
    
    # Other constants
    MTU_SIZE,
    PROTOCOL_UDP,
    TYPE_DATA,
    TYPE_ACK
)


class LinkSimulator:
    """
    Simulates the physical connections between network devices.
    Acts as the "wire" connecting network interfaces.
    """
    
    def __init__(self):
        """Initialize the link simulator with an empty connection map."""
        self.connections = {}  # {(device_name, interface_ip): (device_name, interface_ip)}
        
    def connect(self, device1, interface_ip1, device2, interface_ip2):
        """
        Connect two network interfaces.
        
        Args:
            device1: The first device (Host or Router object)
            interface_ip1: IP address of device1's interface
            device2: The second device (Host or Router object)
            interface_ip2: IP address of device2's interface
        """
        key1 = (device1.name, interface_ip1)
        key2 = (device2.name, interface_ip2)
        self.connections[key1] = key2
        self.connections[key2] = key1
        print(f"[Link] Connected {device1.name} ({interface_ip1}) <-> {device2.name} ({interface_ip2})")
    
    def send(self, frame, sender_device, sender_interface_ip):
        """
        Send a frame from a device to the connected device on the other end.
        
        Args:
            frame: The Frame object to send
            sender_device: The device sending the frame
            sender_interface_ip: The IP address of the sending interface
        """
        sender_key = (sender_device.name, sender_interface_ip)
        
        if sender_key not in self.connections:
            print(f"[Link ERROR] No connection found for {sender_device.name} on {sender_interface_ip}")
            return
        
        # Get the receiver
        receiver_key = self.connections[sender_key]
        receiver_name, receiver_interface_ip = receiver_key
        
        # Find the receiver device object
        # We'll need to register devices with the link simulator
        if not hasattr(self, 'devices'):
            print(f"[Link ERROR] Devices not registered with link simulator")
            return
        
        if receiver_name not in self.devices:
            print(f"[Link ERROR] Device {receiver_name} not found")
            return
        
        receiver_device = self.devices[receiver_name]
        
        # Deliver the frame to the receiver
        print(f"[Link] Frame delivered from {sender_device.name} to {receiver_name}")
        receiver_device.receive_frame(frame, receiver_interface_ip)
    
    def register_device(self, device):
        """Register a device with the link simulator."""
        if not hasattr(self, 'devices'):
            self.devices = {}
        self.devices[device.name] = device


def main():
    """Main function to run the network simulator."""
    
    # Check command line arguments
    if len(sys.argv) != 2:
        print("Usage: python main.py <message_size_bytes>")
        print("Example: python main.py 100")
        sys.exit(1)
    
    try:
        message_size = int(sys.argv[1])
        if message_size < 1:
            print("Error: Message size must be at least 1 byte")
            sys.exit(1)
        if message_size > 10000:
            print("Warning: Large message size, this may take a while...")
    except ValueError:
        print("Error: Message size must be an integer")
        sys.exit(1)
    
    print("=" * 80)
    print("CITS3002 Mini Internet Protocol Stack Simulator")
    print("=" * 80)
    print(f"Starting simulation with {message_size} byte message")
    print()
    
    # Create the link simulator
    link = LinkSimulator()
    
    # Create devices
    print("Creating network devices...")
    
    # Host A
    host_a = Host(
        name="Host A",
        ip_address=HOST_A_IP,
        mac_address=HOST_A_MAC,
        routing_table=ROUTING_TABLE_A,
        link_simulator=link
    )
    
    # Router R1
    router = Router(
        name="Router R1",
        interfaces={R1_IP1: R1_MAC1, R1_IP2: R1_MAC2},
        routing_table=ROUTING_TABLE_R1,
        link_simulator=link
    )
    
    # Host B
    host_b = Host(
        name="Host B",
        ip_address=HOST_B_IP,
        mac_address=HOST_B_MAC,
        routing_table=ROUTING_TABLE_B,
        link_simulator=link
    )
    
    # Register devices with link simulator
    link.register_device(host_a)
    link.register_device(router)
    link.register_device(host_b)
    
    # Create network connections
    print("\nSetting up network connections...")
    link.connect(host_a, HOST_A_IP, router, R1_IP1)
    link.connect(router, R1_IP2, host_b, HOST_B_IP)
    
    print("\n" + "=" * 80)
    print(f"Starting data transmission: {message_size} bytes from Host A to Host B")
    print("=" * 80 + "\n")
    
    # Generate test data
    test_data = "X" * message_size
    
    # Send data from Host A to Host B
    host_a.application_send(
        data=test_data,
        dst_ip=HOST_B_IP,
        dst_port=80,
        src_port=5000
    )
    
    print("\n" + "=" * 80)
    print("Simulation completed")
    print("=" * 80)


if __name__ == "__main__":
    main()