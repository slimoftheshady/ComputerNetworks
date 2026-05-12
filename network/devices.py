from network.protocol import Frame, IPPacket, Segment
from network.config import (
    PROTOCOL_UDP, TYPE_DATA, TYPE_ACK, DEFAULT_TTL,
    MAX_SEGMENT_DATA_SIZE
)


class NetworkNode:
    """Base class for both Host and Router with common functionality."""
    
    def __init__(self, name, link_simulator):
        self.name = name
        self.link_simulator = link_simulator
        self.arp_table = {}  # {ip_address: mac_address}
        self.routing_table = None
        self.interfaces = {}  # {ip_address: mac_address}
    
    def send_frame(self, dst_mac, src_mac, payload, interface_ip):
        """Create and send a Layer 2 frame."""
        print(f"{self.name}: Layer 2: Packet received from Network Layer")
        print(f"{self.name}: Layer 2: Destination MAC lookup for next-hop IP -> {dst_mac}")
        
        frame = Frame(dst_mac, src_mac, payload)
        print(f"{self.name}: Layer 2: Frame created: SRC_MAC={src_mac}, DST_MAC={dst_mac}")
        print(f"{self.name}: Layer 2: Frame sent")
        
        # Send through link simulator
        self.link_simulator.send(frame, self, interface_ip)
    
    def receive_frame(self, frame, interface_ip):
        """Receive a frame from the link layer and process it."""
        print(f"{self.name}: Layer 2: Frame received on {interface_ip}")
        
        # Learn source MAC address
        if frame.src_mac not in self.arp_table.values():
            print(f"{self.name}: Layer 2: Source MAC learned: {frame.src_mac}")
        
        print(f"{self.name}: Layer 2: Packet delivered to Network Layer")
        
        # Deliver payload to Layer 3
        self.receive_packet(frame.payload)
    
    def receive_packet(self, ip_packet):
        """Placeholder - to be overridden by Host and Router."""
        raise NotImplementedError
    
    def send_packet(self, dst_ip, src_ip, ttl, protocol, payload):
        """Create and send a Layer 3 IP packet."""
        print(f"{self.name}: Layer 3: Segment received from Transport Layer: SRC_IP={src_ip}, DST_IP={dst_ip}, TTL={ttl}")
        print(f"{self.name}: Layer 3: Destination IP read: {dst_ip}")
        print(f"{self.name}: Layer 3: Routing table lookup performed")
        
        # Route the packet
        next_hop, out_interface = self.route_packet(dst_ip)
        print(f"{self.name}: Layer 3: Next-hop IP determined: {next_hop}")
        print(f"{self.name}: Layer 3: Outgoing interface selected")
        
        # Find MAC address for next hop
        dst_mac = self.get_mac_address(next_hop)
        
        # Create IP packet
        ip_packet = IPPacket(src_ip, dst_ip, ttl, protocol, payload)
        
        print(f"{self.name}: Layer 3: Packet forwarded to Data Link Layer")
        
        # Send through Layer 2
        src_mac = self.interfaces[out_interface]
        self.send_frame(dst_mac, src_mac, ip_packet.to_bytes(), out_interface)
    
    def route_packet(self, dst_ip):
        """
        Determine next hop and outgoing interface for a destination IP.
        Returns (next_hop_ip, outgoing_interface_ip)
        """
        for route in self.routing_table:
            if self.ip_in_network(dst_ip, route["destination"], route["mask"]):
                if route["next_hop"] is None:
                    # Directly connected - next hop is the destination itself
                    return dst_ip, route["interface"]
                else:
                    return route["next_hop"], route["interface"]
        
        # No route found - default to first interface? In practice, drop packet
        print(f"{self.name}: Layer 3 ERROR: No route to {dst_ip}")
        return None, None
    
    def get_mac_address(self, ip_address):
        """Get MAC address for an IP (simulate ARP)."""
        # Check ARP table
        if ip_address in self.arp_table:
            return self.arp_table[ip_address]
        
        # In a real implementation, would send ARP request
        # Here we'll use a simple mapping based on config
        from network.config import HOST_A_MAC, HOST_B_MAC, R1_MAC1, R1_MAC2
        
        mac_map = {
            "10.0.1.10": HOST_A_MAC,
            "10.0.2.20": HOST_B_MAC,
            "10.0.1.1": R1_MAC1,
            "10.0.2.1": R1_MAC2
        }
        
        if ip_address in mac_map:
            self.arp_table[ip_address] = mac_map[ip_address]
            return mac_map[ip_address]
        
        return None
    
    def ip_in_network(self, ip, network, mask):
        """Check if IP address belongs to a network."""
        ip_parts = [int(x) for x in ip.split('.')]
        net_parts = [int(x) for x in network.split('.')]
        mask_parts = [int(x) for x in mask.split('.')]
        
        for i in range(4):
            if (ip_parts[i] & mask_parts[i]) != (net_parts[i] & mask_parts[i]):
                return False
        return True


class Host(NetworkNode):
    """Host device (end system)."""
    
    def __init__(self, name, ip_address, mac_address, routing_table, link_simulator):
        super().__init__(name, link_simulator)
        self.ip_address = ip_address
        self.mac_address = mac_address
        self.routing_table = routing_table
        self.interfaces = {ip_address: mac_address}
        
        # Transport layer state for rdt2.2
        self.expected_seq = 0  # Next sequence number expected from sender
        self.last_ack_sent = None
        self.pending_segment = None  # For retransmission
        self.waiting_for_ack = False
        self.current_seq = 0
        
        print(f"[DEVICE] {name} created: IP={ip_address}, MAC={mac_address}")
    
    def application_send(self, data, dst_ip, dst_port, src_port):
        """
        Layer 4: Send data from application.
        Handles segmentation and reliable transfer (rdt2.2).
        """
        data_bytes = data.encode('utf-8') if isinstance(data, str) else data
        data_size = len(data_bytes)
        
        print(f"{self.name}: Layer 4: Data received from Application Layer. Data size = {data_size}")
        
        # Segment data if larger than max size
        segments = []
        for i in range(0, data_size, MAX_SEGMENT_DATA_SIZE):
            segment_data = data_bytes[i:i+MAX_SEGMENT_DATA_SIZE]
            segments.append(segment_data)
        
        # Send each segment with rdt2.2
        for i, segment_data in enumerate(segments):
            self.send_segment_with_reliability(
                segment_data, dst_ip, dst_port, src_port, i
            )
    
    def send_segment_with_reliability(self, data_bytes, dst_ip, dst_port, src_port, segment_index):
        """
        Send a segment using rdt2.2 (alternating bit protocol with ACKs).
        """
        seq_num = segment_index % 2  # Alternate between 0 and 1
        
        # Create and send segment
        segment = Segment(src_port, dst_port, TYPE_DATA, seq_num, data_bytes)
        segment.checksum = segment.compute_checksum()
        
        print(f"{self.name}: Layer 4: Checksum computed")
        print(f"{self.name}: Layer 4: Segment created by adding transport layer header (DATA, seq={seq_num}) (encapsulation)")
        print(f"{self.name}: Layer 4: Segment sent to Network Layer")
        
        # Send via Layer 3
        self.send_packet(dst_ip, self.ip_address, DEFAULT_TTL, PROTOCOL_UDP, segment.to_bytes())
        
        # For rdt2.2, we'd wait for ACK and retransmit if needed + since spec says no packet loss, we can assume ACK arrives

    def receive_packet(self, ip_packet):
        """Layer 3: Receive IP packet and deliver to Layer 4."""
        print(f"{self.name}: Layer 3: Packet received from Data Link Layer: SRC_IP={ip_packet.src_ip}, DST_IP={ip_packet.dst_ip}, TTL={ip_packet.ttl}")
        print(f"{self.name}: Layer 3: Destination IP read: {ip_packet.dst_ip}")
        
        if ip_packet.dst_ip == self.ip_address:
            print(f"{self.name}: Layer 3: Packet identified as local delivery")
            print(f"{self.name}: Layer 3: Segment delivered to Transport Layer")
            self.receive_segment(ip_packet.payload)
        else:
            # Not for us - but hosts shouldn't forward in this simple topology
            print(f"{self.name}: Layer 3: Packet not for this host, dropping")
    
    def receive_segment(self, segment_bytes):
        """Layer 4: Receive segment from Layer 3."""
        segment = Segment.from_bytes(segment_bytes)
        
        print(f"{self.name}: Layer 4: Segment received from Network Layer")
        
        # Verify checksum
        if not segment.verify_checksum():
            print(f"{self.name}: Layer 4: Checksum verification failed - segment discarded")
            return
        
        print(f"{self.name}: Layer 4: Checksum verified")
        
        if segment.seg_type == TYPE_DATA:
            # Deliver data to application
            data_str = segment.data.decode('utf-8') if isinstance(segment.data, bytes) else str(segment.data)
            print(f"{self.name}: Layer 4: DATA segment delivered to Application Layer. Data size={len(segment.data)}")
            
            # Send ACK
            self.send_ack(segment.src_port, segment.dst_port, segment.seq_num, segment.src_ip)
            
        elif segment.seg_type == TYPE_ACK:
            print(f"{self.name}: Layer 4: ACK received: seq={segment.seq_num}")
            # In rdt2.2, this would trigger sending next segment
    
    def send_ack(self, dst_port, src_port, ack_seq, dst_ip):
        """Send an ACK segment."""
        ack_segment = Segment(src_port, dst_port, TYPE_ACK, ack_seq, b"")
        ack_segment.checksum = ack_segment.compute_checksum()
        
        print(f"{self.name}: Layer 4: Segment created by adding transport layer header (ACK, seq={ack_seq})")
        print(f"{self.name}: Layer 4: Segment sent to Network Layer")
        
        # Send via Layer 3
        self.send_packet(dst_ip, self.ip_address, DEFAULT_TTL, PROTOCOL_UDP, ack_segment.to_bytes())


class Router(NetworkNode):
    """Router device (forwards packets between networks)."""
    
    def __init__(self, name, interfaces, routing_table, link_simulator):
        super().__init__(name, link_simulator)
        self.interfaces = interfaces  # {ip: mac}
        self.routing_table = routing_table
        self.arp_table = {}  # Will map IP to MAC per interface
        
        print(f"[DEVICE] {name} created: Interfaces={interfaces}")
    
    def receive_packet(self, ip_packet):
        """Layer 3: Receive packet, decrement TTL, and forward."""
        print(f"{self.name}: Layer 3: Packet received from Data Link Layer: SRC_IP={ip_packet.src_ip}, DST_IP={ip_packet.dst_ip}, TTL={ip_packet.ttl}")
        print(f"{self.name}: Layer 3: Destination IP read: {ip_packet.dst_ip}")
        
        # Decrement TTL
        old_ttl = ip_packet.ttl
        ip_packet.decrement_ttl()
        print(f"{self.name}: Layer 3: TTL decremented: {old_ttl} -> {ip_packet.ttl}")
        
        if ip_packet.ttl <= 0:
            print(f"{self.name}: Layer 3: TTL expired - packet dropped")
            return
        
        print(f"{self.name}: Layer 3: Routing table lookup performed")
        
        # Route the packet
        next_hop, out_interface = self.route_packet(ip_packet.dst_ip)
        print(f"{self.name}: Layer 3: Next-hop IP determined: {next_hop}")
        print(f"{self.name}: Layer 3: Outgoing interface selected ({out_interface})")
        
        # Find MAC address for next hop
        dst_mac = self.get_mac_address(next_hop)
        
        # Rebuild packet - TTL already updated
        # Update source MAC to outgoing interface
        src_mac = self.interfaces[out_interface]
        
        print(f"{self.name}: Layer 3: Packet forwarded to Data Link Layer")
        
        # Forward via Layer 2
        self.send_frame(dst_mac, src_mac, ip_packet.to_bytes(), out_interface)
    
    def get_mac_address(self, ip_address):
        """Get MAC address for an IP (simulate ARP)."""
        # Check ARP table
        if ip_address in self.arp_table:
            return self.arp_table[ip_address]
        
        # Simple mapping
        from network.config import HOST_A_MAC, HOST_B_MAC, R1_MAC1, R1_MAC2
        
        mac_map = {
            "10.0.1.10": HOST_A_MAC,
            "10.0.2.20": HOST_B_MAC,
            "10.0.1.1": R1_MAC1,
            "10.0.2.1": R1_MAC2
        }
        
        if ip_address in mac_map:
            self.arp_table[ip_address] = mac_map[ip_address]
            return mac_map[ip_address]
        
        return "FF:FF:FF:FF:FF:FF"  # Broadcast as fallback
