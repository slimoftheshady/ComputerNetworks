#!/usr/bin/env python3
"""
devices.py

This file contains the device classes used in the network simulator.

It includes:
- NetworkNode: a base class with shared network functions
- Host: represents an end device such as Host A or Host B
- Router: represents Router R1, which forwards packets between networks

The purpose of this file is to simulate how devices process data at:
- Layer 2: Data Link Layer
- Layer 3: Network Layer
- Layer 4: Transport Layer

This is only a logical simulation.
No real network communication or socket programming is used.
"""

from network.protocol import EthernetFrame, IPPacket, UDPSegment
from network.config import (
    PROTOCOL_UDP, TYPE_DATA, TYPE_ACK, DEFAULT_TTL,
    MAX_SEGMENT_DATA_SIZE
)


class NetworkNode:
    """
    Base class for both Host and Router.

    This class contains common functionality used by all network devices,
    such as:
    - sending Layer 2 frames
    - receiving Layer 2 frames
    - creating Layer 3 IP packets
    - performing routing table lookups
    - finding MAC addresses using an Address Resolution Protocol-like table

    Host and Router both inherit from this class.
    """

    def __init__(self, name, link_simulator):
        """
        Creates a general network node.

        Parameters:
        - name: the device name, for example "Host A" or "Router R1"
        - link_simulator: the object responsible for logically delivering frames
          between connected devices
        """

        self.name = name
        self.link_simulator = link_simulator

        # Address Resolution Protocol-like table.
        # It maps IP addresses to MAC addresses.
        # Example:
        # {"10.0.1.1": "BB:BB:BB:BB:BB:BB"}
        self.arp_table = {}

        # Routing table used by Layer 3 to decide where to send packets.
        self.routing_table = None

        # Interfaces used by the device.
        # For a host, this usually contains one IP-to-MAC mapping.
        # For a router, this contains multiple interfaces.
        self.interfaces = {}

        # Stores the last next-hop IP address found by Layer 3.
        # Layer 2 uses this value when printing the MAC lookup log.
        self.last_lookup_ip = None

    def send_frame(self, dst_mac, src_mac, payload, interface_ip):
        """
        Layer 2: Create and send an Ethernet-like frame.

        Parameters:
        - dst_mac: destination MAC address for the next-hop device
        - src_mac: source MAC address of the sending interface
        - payload: Layer 3 IP packet carried inside the frame
        - interface_ip: IP address of the interface sending the frame

        This function simulates Layer 2 encapsulation.
        It wraps the Layer 3 packet inside an Ethernet-like frame.
        """

        print(f"{self.name}: Layer 2: Packet received from Network Layer")

        # Print the MAC lookup result.
        # This shows how the next-hop IP address is mapped to a destination MAC.
        if self.last_lookup_ip:
            print(f"{self.name}: Layer 2: Destination MAC lookup for next-hop IP ({self.last_lookup_ip}) → {dst_mac}")
        else:
            print(f"{self.name}: Layer 2: Destination MAC lookup for next-hop IP -> {dst_mac}")

        # Create the Ethernet-like Layer 2 frame.
        frame = EthernetFrame(dst_mac, src_mac, payload)

        print(f"{self.name}: Layer 2: Frame created: SRC_MAC={src_mac}, DST_MAC={dst_mac}")

        # Routers forward frames out a selected interface.
        # Hosts simply send frames out their single interface.
        if self.name == "Router R1":
            if interface_ip == "10.0.1.1":
                interface_display = "Interface 1"
            else:
                interface_display = "Interface 2"

            print(f"{self.name}: Layer 2: Frame forwarded on {interface_display}")
        else:
            print(f"{self.name}: Layer 2: Frame sent")

        # Pass the frame to the link simulator.
        # The link simulator logically delivers the frame to the connected device.
        self.link_simulator.send(frame, self, interface_ip)

    def receive_frame(self, frame, interface_ip):
        """
        Layer 2: Receive an Ethernet-like frame.

        Parameters:
        - frame: the received Ethernet-like frame
        - interface_ip: the receiving interface IP address

        This function simulates the receiving side of Layer 2.
        It learns the source MAC address and then passes the payload
        up to Layer 3.
        """

        # If the receiver is Router R1, show which interface received the frame.
        if self.name == "Router R1":
            if interface_ip == "10.0.1.1":
                interface_display = "Interface 1"
            else:
                interface_display = "Interface 2"

            print(f"{self.name}: Layer 2: Frame received on {interface_display}")

            # Simulate MAC learning.
            # The router learns which source MAC address was seen on which interface.
            print(f"{self.name}: Layer 2: Source MAC learned: {frame.source_mac} on {interface_display}")

        else:
            # Hosts only need to show that a frame was received.
            print(f"{self.name}: Layer 2: Frame received")

            # Simulate MAC learning for hosts.
            print(f"{self.name}: Layer 2: Source MAC learned: {frame.source_mac}")

        print(f"{self.name}: Layer 2: Packet delivered to Network Layer")

        # Remove the Layer 2 frame and pass the Layer 3 payload upward.
        self.receive_packet(frame.payload)

    def receive_packet(self, ip_packet):
        """
        Layer 3: Placeholder method for receiving an IP packet.

        This method is intentionally not implemented in NetworkNode,
        because Host and Router handle received packets differently.

        - Host checks if the packet is meant for itself.
        - Router decrements TTL and forwards the packet.

        Child classes must override this method.
        """

        raise NotImplementedError

    def send_packet(self, dst_ip, src_ip, ttl, protocol, payload):
        """
        Layer 3: Create and send an IP-like packet.

        Parameters:
        - dst_ip: final destination IP address
        - src_ip: source IP address
        - ttl: Time To Live value
        - protocol: transport protocol number, for example UDP
        - payload: Layer 4 segment carried inside the packet

        This function simulates Layer 3 encapsulation.
        It wraps the Layer 4 segment inside an IP-like packet,
        performs routing, and sends the packet down to Layer 2.
        """

        # Create the Layer 3 IP-like packet.
        ip_packet = IPPacket(src_ip, dst_ip, payload, ttl, protocol)

        print(f"{self.name}: Layer 3: Segment received from Transport Layer: SRC_IP={src_ip}, DST_IP={dst_ip}, TTL={ttl}")
        print(f"{self.name}: Layer 3: Destination IP read: {dst_ip}")
        print(f"{self.name}: Layer 3: Routing table lookup performed")

        # Use the routing table to find the next-hop IP and outgoing interface.
        next_hop, out_interface = self.route_packet(dst_ip)

        print(f"{self.name}: Layer 3: Next-hop IP determined: {next_hop}")

        # Show the selected outgoing interface.
        # Router output includes Interface 1 or Interface 2 for clearer logs.
        if self.name == "Router R1":
            if out_interface == "10.0.1.1":
                interface_display = "Interface 1"
            else:
                interface_display = "Interface 2"

            print(f"{self.name}: Layer 3: Outgoing interface selected ({interface_display})")
        else:
            print(f"{self.name}: Layer 3: Outgoing interface selected")

        # Store the next-hop IP address so Layer 2 can display it in the log.
        self.last_lookup_ip = next_hop

        # Find the MAC address of the next-hop device.
        dst_mac = self.get_mac_address(next_hop)

        print(f"{self.name}: Layer 3: Packet forwarded to Data Link Layer")

        # Get the source MAC address of the outgoing interface.
        src_mac = self.interfaces[out_interface]

        # Send the packet down to Layer 2 for framing.
        self.send_frame(dst_mac, src_mac, ip_packet, out_interface)

    def route_packet(self, dst_ip):
        """
        Layer 3: Determine the route for a destination IP address.

        Parameters:
        - dst_ip: the final destination IP address

        Returns:
        - next_hop_ip: the IP address of the next device to send to
        - outgoing_interface_ip: the local interface used to send the packet

        This function checks each route in the routing table.
        If the destination IP matches a route, the route is used.
        """

        for route in self.routing_table:
            # Check whether the destination IP belongs to this route's network.
            if self.ip_in_network(dst_ip, route["destination"], route["mask"]):

                # If next_hop is None, the destination is directly connected.
                # That means the next hop is the destination itself.
                if route["next_hop"] is None:
                    return dst_ip, route["interface"]

                # Otherwise, use the configured next-hop IP address.
                else:
                    return route["next_hop"], route["interface"]

        # If no route matches, the packet cannot be delivered.
        print(f"{self.name}: Layer 3 ERROR: No route to {dst_ip}")
        return None, None

    def get_mac_address(self, ip_address):
        """
        Layer 2: Find the MAC address for a given IP address.

        Parameters:
        - ip_address: the IP address that needs to be converted to a MAC address

        Returns:
        - The matching MAC address if found
        - None if no MAC address is available

        This simulates Address Resolution Protocol behaviour.
        In a real network, Address Resolution Protocol discovers MAC addresses.
        In this simulator, we use a fixed table from config.py.
        """

        # First check whether the MAC address is already known.
        if ip_address in self.arp_table:
            return self.arp_table[ip_address]

        # Import fixed MAC addresses from the configuration file.
        from network.config import HOST_A_MAC, HOST_B_MAC, R1_MAC1, R1_MAC2

        # Static IP-to-MAC mapping for this simple topology.
        mac_map = {
            "10.0.1.10": HOST_A_MAC,
            "10.0.2.20": HOST_B_MAC,
            "10.0.1.1": R1_MAC1,
            "10.0.2.1": R1_MAC2
        }

        # If the IP address exists in the map, save it in the ARP table
        # and return the matching MAC address.
        if ip_address in mac_map:
            self.arp_table[ip_address] = mac_map[ip_address]
            return mac_map[ip_address]

        # If no MAC address is found, return None.
        return None

    def ip_in_network(self, ip, network, mask):
        """
        Layer 3: Check whether an IP address belongs to a network.

        Parameters:
        - ip: the IP address being checked
        - network: the network address
        - mask: the subnet mask

        Returns:
        - True if the IP belongs to the network
        - False otherwise

        Example:
        IP:      10.0.1.10
        Network: 10.0.1.0
        Mask:    255.255.255.0

        Result:
        True
        """

        # Split the dotted decimal IP addresses into four numbers.
        ip_parts = [int(x) for x in ip.split('.')]
        net_parts = [int(x) for x in network.split('.')]
        mask_parts = [int(x) for x in mask.split('.')]

        # Apply the subnet mask to both the IP address and network address.
        # If all masked parts match, the IP belongs to the network.
        for i in range(4):
            if (ip_parts[i] & mask_parts[i]) != (net_parts[i] & mask_parts[i]):
                return False

        return True


class Host(NetworkNode):
    """
    Represents a host device.

    In this project, Host A and Host B are end devices.

    A Host can:
    - send application data
    - create Layer 4 DATA segments
    - send packets to the router
    - receive packets meant for itself
    - verify checksums
    - deliver data to the application layer
    - send and receive ACK segments
    """

    def __init__(self, name, ip_address, mac_address, routing_table, link_simulator):
        """
        Creates a host device.

        Parameters:
        - name: host name, for example "Host A"
        - ip_address: host IP address
        - mac_address: host MAC address
        - routing_table: routing table used by the host
        - link_simulator: object used to deliver frames between devices
        """

        # Initialise the common NetworkNode properties.
        super().__init__(name, link_simulator)

        self.ip_address = ip_address
        self.mac_address = mac_address
        self.routing_table = routing_table

        # A host has one interface in this simple topology.
        self.interfaces = {ip_address: mac_address}

        # Transport layer state for reliable data transfer 2.2.
        # expected_seq stores the next DATA sequence number expected.
        self.expected_seq = 0

        # Stores the last acknowledgement sent by this host.
        self.last_ack_sent = None

        # Stores a segment that may need retransmission.
        self.pending_segment = None

        # Tracks whether this host is waiting for an acknowledgement.
        self.waiting_for_ack = False

        # Current sequence number used by the sender.
        self.current_seq = 0

        print(f"[DEVICE] {name} created: IP={ip_address}, MAC={mac_address}")

    def application_send(self, data, dst_ip, dst_port, src_port):
        """
        Layer 4: Receive data from the application layer and send it.

        Parameters:
        - data: application message to send
        - dst_ip: destination IP address
        - dst_port: destination application port
        - src_port: source application port

        This function:
        1. Receives application data.
        2. Converts the data to bytes if needed.
        3. Splits the data into segments if it is larger than the maximum size.
        4. Sends each segment using reliable data transfer 2.2.
        """

        # Convert string data into bytes.
        # If data is already bytes, keep it unchanged.
        data_bytes = data.encode('utf-8') if isinstance(data, str) else data

        # Calculate the full application data size.
        data_size = len(data_bytes)

        print(f"{self.name}: Layer 4: Data received from Application Layer. Data size={data_size}")

        # Split data into multiple segments if it is larger than 500 bytes.
        segments = []

        for i in range(0, data_size, MAX_SEGMENT_DATA_SIZE):
            segment_data = data_bytes[i:i + MAX_SEGMENT_DATA_SIZE]
            segments.append(segment_data)

        # Send each segment one by one.
        # The sequence number alternates using the segment index.
        for i, segment_data in enumerate(segments):
            self.send_segment_with_reliability(
                segment_data, dst_ip, dst_port, src_port, i
            )

    def send_segment_with_reliability(self, data_bytes, dst_ip, dst_port, src_port, segment_index):
        """
        Layer 4: Send one DATA segment using reliable data transfer 2.2.

        Parameters:
        - data_bytes: the data carried in this segment
        - dst_ip: destination IP address
        - dst_port: destination port number
        - src_port: source port number
        - segment_index: position of the segment in the full message

        The assignment uses the Alternating Bit Protocol.
        This means sequence numbers alternate between 0 and 1.
        """

        # Alternate the sequence number between 0 and 1.
        # Example: segment 0 uses seq 0, segment 1 uses seq 1, segment 2 uses seq 0.
        seq_num = segment_index % 2

        # Create a Layer 4 DATA segment.
        segment = UDPSegment(src_port, dst_port, data_bytes, TYPE_DATA, seq_num)

        print(f"{self.name}: Layer 4: Checksum computed")
        print(f"{self.name}: Layer 4: Segment created by adding transport layer header (DATA, seq={seq_num}) (encapsulation)")
        print(f"{self.name}: Layer 4: Segment sent to Network Layer")

        # Send the Layer 4 segment down to Layer 3.
        self.send_packet(dst_ip, self.ip_address, DEFAULT_TTL, PROTOCOL_UDP, segment)

    def receive_packet(self, ip_packet):
        """
        Layer 3: Receive an IP-like packet from Layer 2.

        Parameters:
        - ip_packet: the received Layer 3 packet

        The host checks whether the destination IP matches its own IP address.
        If yes, it delivers the payload to Layer 4.
        If not, it drops the packet because hosts do not forward packets.
        """

        print(f"{self.name}: Layer 3: Packet received from Data Link Layer: SRC_IP={ip_packet.source_ip}, DST_IP={ip_packet.destination_ip}, TTL={ip_packet.ttl}")
        print(f"{self.name}: Layer 3: Destination IP read: {ip_packet.destination_ip}")

        # Check whether this packet is meant for this host.
        if ip_packet.destination_ip == self.ip_address:
            print(f"{self.name}: Layer 3: Packet identified as local delivery")
            print(f"{self.name}: Layer 3: Segment delivered to Transport Layer")

            # Pass the Layer 4 segment upward.
            self.receive_segment(ip_packet.payload, ip_packet.source_ip)

        else:
            # In this project, hosts are end devices.
            # They should not forward packets like routers do.
            print(f"{self.name}: Layer 3: Packet not for this host, dropping")

    def receive_segment(self, segment, src_ip):
        """
        Layer 4: Receive a UDP-like segment from Layer 3.

        Parameters:
        - segment: the Layer 4 segment
        - src_ip: IP address of the sender

        This function:
        1. Receives the segment.
        2. Verifies the checksum.
        3. If it is DATA, delivers data to the application layer and sends ACK.
        4. If it is ACK, logs that the acknowledgement was received.
        """

        print(f"{self.name}: Layer 4: Segment received from Network Layer")

        # Verify the checksum before accepting the segment.
        # If the checksum is wrong, the segment is considered corrupted.
        if not segment.verify_checksum():
            print(f"{self.name}: Layer 4: Checksum verification failed - segment discarded")
            return

        print(f"{self.name}: Layer 4: Checksum verified")

        # If the received segment contains application data,
        # deliver it to the application layer and send an ACK.
        if segment.is_data():

            # Convert the data to string only for readability if needed.
            # The variable is not used later because the required output only needs data size.
            data_str = segment.data.decode('utf-8') if isinstance(segment.data, bytes) else str(segment.data)

            print(f"{self.name}: Layer 4: DATA segment delivered to Application Layer. Data size={len(segment.data)}")

            # Send an acknowledgement with the same sequence number.
            self.send_ack(segment.source_port, segment.destination_port, segment.sequence_number, src_ip)

        # If the received segment is an ACK, the sender knows the DATA segment arrived.
        elif segment.is_ack():
            print(f"{self.name}: Layer 4: ACK received: seq={segment.sequence_number}")

    def send_ack(self, dst_port, src_port, ack_seq, dst_ip):
        """
        Layer 4: Create and send an ACK segment.

        Parameters:
        - dst_port: destination port for the ACK
        - src_port: source port for the ACK
        - ack_seq: acknowledgement sequence number
        - dst_ip: destination IP address for the ACK

        ACK segments contain no application data.
        They confirm that a DATA segment was received correctly.
        """

        # Create a Layer 4 ACK segment.
        # The data field is empty because ACKs do not carry application data.
        ack_segment = UDPSegment(src_port, dst_port, b"", TYPE_ACK, ack_seq)

        print(f"{self.name}: Layer 4: Segment created by adding transport layer header (ACK, seq={ack_seq})")
        print(f"{self.name}: Layer 4: Segment sent to Network Layer")

        # Send the ACK down to Layer 3.
        self.send_packet(dst_ip, self.ip_address, DEFAULT_TTL, PROTOCOL_UDP, ack_segment)


class Router(NetworkNode):
    """
    Represents Router R1.

    The router connects Network 1 and Network 2.

    Router R1 can:
    - receive Layer 2 frames
    - extract Layer 3 packets
    - read destination IP addresses
    - decrement Time To Live
    - perform routing table lookup
    - forward packets out the correct interface
    - create new Layer 2 frames for the next hop
    """

    def __init__(self, name, interfaces, routing_table, link_simulator):
        """
        Creates a router device.

        Parameters:
        - name: router name, for example "Router R1"
        - interfaces: router interfaces, mapping interface IP addresses to MAC addresses
        - routing_table: routing table used to forward packets
        - link_simulator: object used to deliver frames between devices
        """

        # Initialise the common NetworkNode properties.
        super().__init__(name, link_simulator)

        # Router has multiple interfaces.
        # Example:
        # {
        #     "10.0.1.1": "BB:BB:BB:BB:BB:BB",
        #     "10.0.2.1": "CC:CC:CC:CC:CC:CC"
        # }
        self.interfaces = interfaces

        # Routing table used to decide outgoing interface and next hop.
        self.routing_table = routing_table

        # Router also keeps an Address Resolution Protocol-like table.
        self.arp_table = {}

        print(f"[DEVICE] {name} created: Interfaces={interfaces}")

    def receive_packet(self, ip_packet):
        """
        Layer 3: Receive, process, and forward an IP-like packet.

        Parameters:
        - ip_packet: the received Layer 3 packet

        The router does not deliver the segment to Layer 4.
        Instead, it:
        1. Reads the destination IP address.
        2. Decrements Time To Live.
        3. Drops the packet if Time To Live expires.
        4. Performs routing table lookup.
        5. Sends the packet back down to Layer 2 for forwarding.
        """

        print(f"{self.name}: Layer 3: Packet received from Data Link Layer: SRC_IP={ip_packet.source_ip}, DST_IP={ip_packet.destination_ip}, TTL={ip_packet.ttl}")
        print(f"{self.name}: Layer 3: Destination IP read: {ip_packet.destination_ip}")

        # Decrement Time To Live because the packet is passing through a router.
        old_ttl = ip_packet.ttl

        # If Time To Live becomes 0, the packet must be dropped.
        if not ip_packet.decrement_ttl():
            print(f"{self.name}: Layer 3: TTL expired - packet dropped")
            return

        print(f"{self.name}: Layer 3: TTL decremented: {old_ttl} -> {ip_packet.ttl}")
        print(f"{self.name}: Layer 3: Routing table lookup performed")

        # Use the routing table to decide the next hop and outgoing interface.
        next_hop, out_interface = self.route_packet(ip_packet.destination_ip)

        print(f"{self.name}: Layer 3: Next-hop IP determined: {next_hop}")

        # Convert the outgoing interface IP into a readable interface name.
        if out_interface == "10.0.1.1":
            interface_display = "Interface 1"
        else:
            interface_display = "Interface 2"

        print(f"{self.name}: Layer 3: Outgoing interface selected ({interface_display})")

        # Store next-hop IP for Layer 2 MAC lookup logging.
        self.last_lookup_ip = next_hop

        # Find the destination MAC address for the next hop.
        dst_mac = self.get_mac_address(next_hop)

        print(f"{self.name}: Layer 3: Packet forwarded to Data Link Layer")

        # Get the router interface MAC address used as the source MAC.
        src_mac = self.interfaces[out_interface]

        # Send the packet to Layer 2 for forwarding.
        self.send_frame(dst_mac, src_mac, ip_packet, out_interface)

    def get_mac_address(self, ip_address):
        """
        Layer 2: Find the MAC address for a given IP address.

        Parameters:
        - ip_address: the IP address of the next-hop device

        Returns:
        - the matching MAC address if found
        - broadcast MAC address as a fallback if not found

        This function simulates Address Resolution Protocol behaviour
        using a fixed mapping from config.py.
        """

        # First check whether the router already knows this IP-to-MAC mapping.
        if ip_address in self.arp_table:
            return self.arp_table[ip_address]

        # Import fixed MAC addresses from the configuration file.
        from network.config import HOST_A_MAC, HOST_B_MAC, R1_MAC1, R1_MAC2

        # Static IP-to-MAC mapping for the whole topology.
        mac_map = {
            "10.0.1.10": HOST_A_MAC,
            "10.0.2.20": HOST_B_MAC,
            "10.0.1.1": R1_MAC1,
            "10.0.2.1": R1_MAC2
        }

        # If the IP address is found, save it in the router's ARP table.
        if ip_address in mac_map:
            self.arp_table[ip_address] = mac_map[ip_address]
            return mac_map[ip_address]

        # If the MAC address cannot be found, return a broadcast MAC address.
        # This is only a fallback for the simulation.
        return "FF:FF:FF:FF:FF:FF"#!/usr/bin/env python3
"""
devices.py

This file contains the device classes used in the network simulator.

It includes:
- NetworkNode: a base class with shared network functions
- Host: represents an end device such as Host A or Host B
- Router: represents Router R1, which forwards packets between networks

The purpose of this file is to simulate how devices process data at:
- Layer 2: Data Link Layer
- Layer 3: Network Layer
- Layer 4: Transport Layer

This is only a logical simulation.
No real network communication or socket programming is used.
"""

from network.protocol import EthernetFrame, IPPacket, UDPSegment
from network.config import (
    PROTOCOL_UDP, TYPE_DATA, TYPE_ACK, DEFAULT_TTL,
    MAX_SEGMENT_DATA_SIZE
)


class NetworkNode:
    """
    Base class for both Host and Router.

    This class contains common functionality used by all network devices,
    such as:
    - sending Layer 2 frames
    - receiving Layer 2 frames
    - creating Layer 3 IP packets
    - performing routing table lookups
    - finding MAC addresses using an Address Resolution Protocol-like table

    Host and Router both inherit from this class.
    """

    def __init__(self, name, link_simulator):
        """
        Creates a general network node.

        Parameters:
        - name: the device name, for example "Host A" or "Router R1"
        - link_simulator: the object responsible for logically delivering frames
          between connected devices
        """

        self.name = name
        self.link_simulator = link_simulator

        # Address Resolution Protocol-like table.
        # It maps IP addresses to MAC addresses.
        # Example:
        # {"10.0.1.1": "BB:BB:BB:BB:BB:BB"}
        self.arp_table = {}

        # Routing table used by Layer 3 to decide where to send packets.
        self.routing_table = None

        # Interfaces used by the device.
        # For a host, this usually contains one IP-to-MAC mapping.
        # For a router, this contains multiple interfaces.
        self.interfaces = {}

        # Stores the last next-hop IP address found by Layer 3.
        # Layer 2 uses this value when printing the MAC lookup log.
        self.last_lookup_ip = None

    def send_frame(self, dst_mac, src_mac, payload, interface_ip):
        """
        Layer 2: Create and send an Ethernet-like frame.

        Parameters:
        - dst_mac: destination MAC address for the next-hop device
        - src_mac: source MAC address of the sending interface
        - payload: Layer 3 IP packet carried inside the frame
        - interface_ip: IP address of the interface sending the frame

        This function simulates Layer 2 encapsulation.
        It wraps the Layer 3 packet inside an Ethernet-like frame.
        """

        print(f"{self.name}: Layer 2: Packet received from Network Layer")

        # Print the MAC lookup result.
        # This shows how the next-hop IP address is mapped to a destination MAC.
        if self.last_lookup_ip:
            print(f"{self.name}: Layer 2: Destination MAC lookup for next-hop IP ({self.last_lookup_ip}) → {dst_mac}")
        else:
            print(f"{self.name}: Layer 2: Destination MAC lookup for next-hop IP -> {dst_mac}")

        # Create the Ethernet-like Layer 2 frame.
        frame = EthernetFrame(dst_mac, src_mac, payload)

        print(f"{self.name}: Layer 2: Frame created: SRC_MAC={src_mac}, DST_MAC={dst_mac}")

        # Routers forward frames out a selected interface.
        # Hosts simply send frames out their single interface.
        if self.name == "Router R1":
            if interface_ip == "10.0.1.1":
                interface_display = "Interface 1"
            else:
                interface_display = "Interface 2"

            print(f"{self.name}: Layer 2: Frame forwarded on {interface_display}")
        else:
            print(f"{self.name}: Layer 2: Frame sent")

        # Pass the frame to the link simulator.
        # The link simulator logically delivers the frame to the connected device.
        self.link_simulator.send(frame, self, interface_ip)

    def receive_frame(self, frame, interface_ip):
        """
        Layer 2: Receive an Ethernet-like frame.

        Parameters:
        - frame: the received Ethernet-like frame
        - interface_ip: the receiving interface IP address

        This function simulates the receiving side of Layer 2.
        It learns the source MAC address and then passes the payload
        up to Layer 3.
        """

        # If the receiver is Router R1, show which interface received the frame.
        if self.name == "Router R1":
            if interface_ip == "10.0.1.1":
                interface_display = "Interface 1"
            else:
                interface_display = "Interface 2"

            print(f"{self.name}: Layer 2: Frame received on {interface_display}")

            # Simulate MAC learning.
            # The router learns which source MAC address was seen on which interface.
            print(f"{self.name}: Layer 2: Source MAC learned: {frame.source_mac} on {interface_display}")

        else:
            # Hosts only need to show that a frame was received.
            print(f"{self.name}: Layer 2: Frame received")

            # Simulate MAC learning for hosts.
            print(f"{self.name}: Layer 2: Source MAC learned: {frame.source_mac}")

        print(f"{self.name}: Layer 2: Packet delivered to Network Layer")

        # Remove the Layer 2 frame and pass the Layer 3 payload upward.
        self.receive_packet(frame.payload)

    def receive_packet(self, ip_packet):
        """
        Layer 3: Placeholder method for receiving an IP packet.

        This method is intentionally not implemented in NetworkNode,
        because Host and Router handle received packets differently.

        - Host checks if the packet is meant for itself.
        - Router decrements TTL and forwards the packet.

        Child classes must override this method.
        """

        raise NotImplementedError

    def send_packet(self, dst_ip, src_ip, ttl, protocol, payload):
        """
        Layer 3: Create and send an IP-like packet.

        Parameters:
        - dst_ip: final destination IP address
        - src_ip: source IP address
        - ttl: Time To Live value
        - protocol: transport protocol number, for example UDP
        - payload: Layer 4 segment carried inside the packet

        This function simulates Layer 3 encapsulation.
        It wraps the Layer 4 segment inside an IP-like packet,
        performs routing, and sends the packet down to Layer 2.
        """

        # Create the Layer 3 IP-like packet.
        ip_packet = IPPacket(src_ip, dst_ip, payload, ttl, protocol)

        print(f"{self.name}: Layer 3: Segment received from Transport Layer: SRC_IP={src_ip}, DST_IP={dst_ip}, TTL={ttl}")
        print(f"{self.name}: Layer 3: Destination IP read: {dst_ip}")
        print(f"{self.name}: Layer 3: Routing table lookup performed")

        # Use the routing table to find the next-hop IP and outgoing interface.
        next_hop, out_interface = self.route_packet(dst_ip)

        print(f"{self.name}: Layer 3: Next-hop IP determined: {next_hop}")

        # Show the selected outgoing interface.
        # Router output includes Interface 1 or Interface 2 for clearer logs.
        if self.name == "Router R1":
            if out_interface == "10.0.1.1":
                interface_display = "Interface 1"
            else:
                interface_display = "Interface 2"

            print(f"{self.name}: Layer 3: Outgoing interface selected ({interface_display})")
        else:
            print(f"{self.name}: Layer 3: Outgoing interface selected")

        # Store the next-hop IP address so Layer 2 can display it in the log.
        self.last_lookup_ip = next_hop

        # Find the MAC address of the next-hop device.
        dst_mac = self.get_mac_address(next_hop)

        print(f"{self.name}: Layer 3: Packet forwarded to Data Link Layer")

        # Get the source MAC address of the outgoing interface.
        src_mac = self.interfaces[out_interface]

        # Send the packet down to Layer 2 for framing.
        self.send_frame(dst_mac, src_mac, ip_packet, out_interface)

    def route_packet(self, dst_ip):
        """
        Layer 3: Determine the route for a destination IP address.

        Parameters:
        - dst_ip: the final destination IP address

        Returns:
        - next_hop_ip: the IP address of the next device to send to
        - outgoing_interface_ip: the local interface used to send the packet

        This function checks each route in the routing table.
        If the destination IP matches a route, the route is used.
        """

        for route in self.routing_table:
            # Check whether the destination IP belongs to this route's network.
            if self.ip_in_network(dst_ip, route["destination"], route["mask"]):

                # If next_hop is None, the destination is directly connected.
                # That means the next hop is the destination itself.
                if route["next_hop"] is None:
                    return dst_ip, route["interface"]

                # Otherwise, use the configured next-hop IP address.
                else:
                    return route["next_hop"], route["interface"]

        # If no route matches, the packet cannot be delivered.
        print(f"{self.name}: Layer 3 ERROR: No route to {dst_ip}")
        return None, None

    def get_mac_address(self, ip_address):
        """
        Layer 2: Find the MAC address for a given IP address.

        Parameters:
        - ip_address: the IP address that needs to be converted to a MAC address

        Returns:
        - The matching MAC address if found
        - None if no MAC address is available

        This simulates Address Resolution Protocol behaviour.
        In a real network, Address Resolution Protocol discovers MAC addresses.
        In this simulator, we use a fixed table from config.py.
        """

        # First check whether the MAC address is already known.
        if ip_address in self.arp_table:
            return self.arp_table[ip_address]

        # Import fixed MAC addresses from the configuration file.
        from network.config import HOST_A_MAC, HOST_B_MAC, R1_MAC1, R1_MAC2

        # Static IP-to-MAC mapping for this simple topology.
        mac_map = {
            "10.0.1.10": HOST_A_MAC,
            "10.0.2.20": HOST_B_MAC,
            "10.0.1.1": R1_MAC1,
            "10.0.2.1": R1_MAC2
        }

        # If the IP address exists in the map, save it in the ARP table
        # and return the matching MAC address.
        if ip_address in mac_map:
            self.arp_table[ip_address] = mac_map[ip_address]
            return mac_map[ip_address]

        # If no MAC address is found, return None.
        return None

    def ip_in_network(self, ip, network, mask):
        """
        Layer 3: Check whether an IP address belongs to a network.

        Parameters:
        - ip: the IP address being checked
        - network: the network address
        - mask: the subnet mask

        Returns:
        - True if the IP belongs to the network
        - False otherwise

        Example:
        IP:      10.0.1.10
        Network: 10.0.1.0
        Mask:    255.255.255.0

        Result:
        True
        """

        # Split the dotted decimal IP addresses into four numbers.
        ip_parts = [int(x) for x in ip.split('.')]
        net_parts = [int(x) for x in network.split('.')]
        mask_parts = [int(x) for x in mask.split('.')]

        # Apply the subnet mask to both the IP address and network address.
        # If all masked parts match, the IP belongs to the network.
        for i in range(4):
            if (ip_parts[i] & mask_parts[i]) != (net_parts[i] & mask_parts[i]):
                return False

        return True


class Host(NetworkNode):
    """
    Represents a host device.

    In this project, Host A and Host B are end devices.

    A Host can:
    - send application data
    - create Layer 4 DATA segments
    - send packets to the router
    - receive packets meant for itself
    - verify checksums
    - deliver data to the application layer
    - send and receive ACK segments
    """

    def __init__(self, name, ip_address, mac_address, routing_table, link_simulator):
        """
        Creates a host device.

        Parameters:
        - name: host name, for example "Host A"
        - ip_address: host IP address
        - mac_address: host MAC address
        - routing_table: routing table used by the host
        - link_simulator: object used to deliver frames between devices
        """

        # Initialise the common NetworkNode properties.
        super().__init__(name, link_simulator)

        self.ip_address = ip_address
        self.mac_address = mac_address
        self.routing_table = routing_table

        # A host has one interface in this simple topology.
        self.interfaces = {ip_address: mac_address}

        # Transport layer state for reliable data transfer 2.2.
        # expected_seq stores the next DATA sequence number expected.
        self.expected_seq = 0

        # Stores the last acknowledgement sent by this host.
        self.last_ack_sent = None

        # Stores a segment that may need retransmission.
        self.pending_segment = None

        # Tracks whether this host is waiting for an acknowledgement.
        self.waiting_for_ack = False

        # Current sequence number used by the sender.
        self.current_seq = 0

        print(f"[DEVICE] {name} created: IP={ip_address}, MAC={mac_address}")

    def application_send(self, data, dst_ip, dst_port, src_port):
        """
        Layer 4: Receive data from the application layer and send it.

        Parameters:
        - data: application message to send
        - dst_ip: destination IP address
        - dst_port: destination application port
        - src_port: source application port

        This function:
        1. Receives application data.
        2. Converts the data to bytes if needed.
        3. Splits the data into segments if it is larger than the maximum size.
        4. Sends each segment using reliable data transfer 2.2.
        """

        # Convert string data into bytes.
        # If data is already bytes, keep it unchanged.
        data_bytes = data.encode('utf-8') if isinstance(data, str) else data

        # Calculate the full application data size.
        data_size = len(data_bytes)

        print(f"{self.name}: Layer 4: Data received from Application Layer. Data size={data_size}")

        # Split data into multiple segments if it is larger than 500 bytes.
        segments = []

        for i in range(0, data_size, MAX_SEGMENT_DATA_SIZE):
            segment_data = data_bytes[i:i + MAX_SEGMENT_DATA_SIZE]
            segments.append(segment_data)

        # Send each segment one by one.
        # The sequence number alternates using the segment index.
        for i, segment_data in enumerate(segments):
            self.send_segment_with_reliability(
                segment_data, dst_ip, dst_port, src_port, i
            )

    def send_segment_with_reliability(self, data_bytes, dst_ip, dst_port, src_port, segment_index):
        """
        Layer 4: Send one DATA segment using reliable data transfer 2.2.

        Parameters:
        - data_bytes: the data carried in this segment
        - dst_ip: destination IP address
        - dst_port: destination port number
        - src_port: source port number
        - segment_index: position of the segment in the full message

        The assignment uses the Alternating Bit Protocol.
        This means sequence numbers alternate between 0 and 1.
        """

        # Alternate the sequence number between 0 and 1.
        # Example: segment 0 uses seq 0, segment 1 uses seq 1, segment 2 uses seq 0.
        seq_num = segment_index % 2

        # Create a Layer 4 DATA segment.
        segment = UDPSegment(src_port, dst_port, data_bytes, TYPE_DATA, seq_num)

        print(f"{self.name}: Layer 4: Checksum computed")
        print(f"{self.name}: Layer 4: Segment created by adding transport layer header (DATA, seq={seq_num}) (encapsulation)")
        print(f"{self.name}: Layer 4: Segment sent to Network Layer")

        # Send the Layer 4 segment down to Layer 3.
        self.send_packet(dst_ip, self.ip_address, DEFAULT_TTL, PROTOCOL_UDP, segment)

    def receive_packet(self, ip_packet):
        """
        Layer 3: Receive an IP-like packet from Layer 2.

        Parameters:
        - ip_packet: the received Layer 3 packet

        The host checks whether the destination IP matches its own IP address.
        If yes, it delivers the payload to Layer 4.
        If not, it drops the packet because hosts do not forward packets.
        """

        print(f"{self.name}: Layer 3: Packet received from Data Link Layer: SRC_IP={ip_packet.source_ip}, DST_IP={ip_packet.destination_ip}, TTL={ip_packet.ttl}")
        print(f"{self.name}: Layer 3: Destination IP read: {ip_packet.destination_ip}")

        # Check whether this packet is meant for this host.
        if ip_packet.destination_ip == self.ip_address:
            print(f"{self.name}: Layer 3: Packet identified as local delivery")
            print(f"{self.name}: Layer 3: Segment delivered to Transport Layer")

            # Pass the Layer 4 segment upward.
            self.receive_segment(ip_packet.payload, ip_packet.source_ip)

        else:
            # In this project, hosts are end devices.
            # They should not forward packets like routers do.
            print(f"{self.name}: Layer 3: Packet not for this host, dropping")

    def receive_segment(self, segment, src_ip):
        """
        Layer 4: Receive a UDP-like segment from Layer 3.

        Parameters:
        - segment: the Layer 4 segment
        - src_ip: IP address of the sender

        This function:
        1. Receives the segment.
        2. Verifies the checksum.
        3. If it is DATA, delivers data to the application layer and sends ACK.
        4. If it is ACK, logs that the acknowledgement was received.
        """

        print(f"{self.name}: Layer 4: Segment received from Network Layer")

        # Verify the checksum before accepting the segment.
        # If the checksum is wrong, the segment is considered corrupted.
        if not segment.verify_checksum():
            print(f"{self.name}: Layer 4: Checksum verification failed - segment discarded")
            return

        print(f"{self.name}: Layer 4: Checksum verified")

        # If the received segment contains application data,
        # deliver it to the application layer and send an ACK.
        if segment.is_data():

            # Convert the data to string only for readability if needed.
            # The variable is not used later because the required output only needs data size.
            data_str = segment.data.decode('utf-8') if isinstance(segment.data, bytes) else str(segment.data)

            print(f"{self.name}: Layer 4: DATA segment delivered to Application Layer. Data size={len(segment.data)}")

            # Send an acknowledgement with the same sequence number.
            self.send_ack(segment.source_port, segment.destination_port, segment.sequence_number, src_ip)

        # If the received segment is an ACK, the sender knows the DATA segment arrived.
        elif segment.is_ack():
            print(f"{self.name}: Layer 4: ACK received: seq={segment.sequence_number}")

    def send_ack(self, dst_port, src_port, ack_seq, dst_ip):
        """
        Layer 4: Create and send an ACK segment.

        Parameters:
        - dst_port: destination port for the ACK
        - src_port: source port for the ACK
        - ack_seq: acknowledgement sequence number
        - dst_ip: destination IP address for the ACK

        ACK segments contain no application data.
        They confirm that a DATA segment was received correctly.
        """

        # Create a Layer 4 ACK segment.
        # The data field is empty because ACKs do not carry application data.
        ack_segment = UDPSegment(src_port, dst_port, b"", TYPE_ACK, ack_seq)

        print(f"{self.name}: Layer 4: Segment created by adding transport layer header (ACK, seq={ack_seq})")
        print(f"{self.name}: Layer 4: Segment sent to Network Layer")

        # Send the ACK down to Layer 3.
        self.send_packet(dst_ip, self.ip_address, DEFAULT_TTL, PROTOCOL_UDP, ack_segment)


class Router(NetworkNode):
    """
    Represents Router R1.

    The router connects Network 1 and Network 2.

    Router R1 can:
    - receive Layer 2 frames
    - extract Layer 3 packets
    - read destination IP addresses
    - decrement Time To Live
    - perform routing table lookup
    - forward packets out the correct interface
    - create new Layer 2 frames for the next hop
    """

    def __init__(self, name, interfaces, routing_table, link_simulator):
        """
        Creates a router device.

        Parameters:
        - name: router name, for example "Router R1"
        - interfaces: router interfaces, mapping interface IP addresses to MAC addresses
        - routing_table: routing table used to forward packets
        - link_simulator: object used to deliver frames between devices
        """

        # Initialise the common NetworkNode properties.
        super().__init__(name, link_simulator)

        # Router has multiple interfaces.
        # Example:
        # {
        #     "10.0.1.1": "BB:BB:BB:BB:BB:BB",
        #     "10.0.2.1": "CC:CC:CC:CC:CC:CC"
        # }
        self.interfaces = interfaces

        # Routing table used to decide outgoing interface and next hop.
        self.routing_table = routing_table

        # Router also keeps an Address Resolution Protocol-like table.
        self.arp_table = {}

        print(f"[DEVICE] {name} created: Interfaces={interfaces}")

    def receive_packet(self, ip_packet):
        """
        Layer 3: Receive, process, and forward an IP-like packet.

        Parameters:
        - ip_packet: the received Layer 3 packet

        The router does not deliver the segment to Layer 4.
        Instead, it:
        1. Reads the destination IP address.
        2. Decrements Time To Live.
        3. Drops the packet if Time To Live expires.
        4. Performs routing table lookup.
        5. Sends the packet back down to Layer 2 for forwarding.
        """

        print(f"{self.name}: Layer 3: Packet received from Data Link Layer: SRC_IP={ip_packet.source_ip}, DST_IP={ip_packet.destination_ip}, TTL={ip_packet.ttl}")
        print(f"{self.name}: Layer 3: Destination IP read: {ip_packet.destination_ip}")

        # Decrement Time To Live because the packet is passing through a router.
        old_ttl = ip_packet.ttl

        # If Time To Live becomes 0, the packet must be dropped.
        if not ip_packet.decrement_ttl():
            print(f"{self.name}: Layer 3: TTL expired - packet dropped")
            return

        print(f"{self.name}: Layer 3: TTL decremented: {old_ttl} -> {ip_packet.ttl}")
        print(f"{self.name}: Layer 3: Routing table lookup performed")

        # Use the routing table to decide the next hop and outgoing interface.
        next_hop, out_interface = self.route_packet(ip_packet.destination_ip)

        print(f"{self.name}: Layer 3: Next-hop IP determined: {next_hop}")

        # Convert the outgoing interface IP into a readable interface name.
        if out_interface == "10.0.1.1":
            interface_display = "Interface 1"
        else:
            interface_display = "Interface 2"

        print(f"{self.name}: Layer 3: Outgoing interface selected ({interface_display})")

        # Store next-hop IP for Layer 2 MAC lookup logging.
        self.last_lookup_ip = next_hop

        # Find the destination MAC address for the next hop.
        dst_mac = self.get_mac_address(next_hop)

        print(f"{self.name}: Layer 3: Packet forwarded to Data Link Layer")

        # Get the router interface MAC address used as the source MAC.
        src_mac = self.interfaces[out_interface]

        # Send the packet to Layer 2 for forwarding.
        self.send_frame(dst_mac, src_mac, ip_packet, out_interface)

    def get_mac_address(self, ip_address):
        """
        Layer 2: Find the MAC address for a given IP address.

        Parameters:
        - ip_address: the IP address of the next-hop device

        Returns:
        - the matching MAC address if found
        - broadcast MAC address as a fallback if not found

        This function simulates Address Resolution Protocol behaviour
        using a fixed mapping from config.py.
        """

        # First check whether the router already knows this IP-to-MAC mapping.
        if ip_address in self.arp_table:
            return self.arp_table[ip_address]

        # Import fixed MAC addresses from the configuration file.
        from network.config import HOST_A_MAC, HOST_B_MAC, R1_MAC1, R1_MAC2

        # Static IP-to-MAC mapping for the whole topology.
        mac_map = {
            "10.0.1.10": HOST_A_MAC,
            "10.0.2.20": HOST_B_MAC,
            "10.0.1.1": R1_MAC1,
            "10.0.2.1": R1_MAC2
        }

        # If the IP address is found, save it in the router's ARP table.
        if ip_address in mac_map:
            self.arp_table[ip_address] = mac_map[ip_address]
            return mac_map[ip_address]

        # If the MAC address cannot be found, return a broadcast MAC address.
        # This is only a fallback for the simulation.
        return "FF:FF:FF:FF:FF:FF"
