
"""
protocol.py

This file contains the protocol header definitions and classes for:
- Layer 2: Ethernet-like Frame
- Layer 3: IP-like Packet
- Layer 4: UDP-like Segment with ACK support

These classes do not perform full network behaviour.
They only represent the data structures used by the Host and Router classes.
"""

# Ethernet Type value for IPv4 payload
ETH_TYPE_IPV4 = 0x0800

# IP Protocol value for UDP payload
IP_PROTOCOL_UDP = 17

# Transport segment types
DATA = 0
ACK = 1


class EthernetFrame:
    """
    Represents a Layer 2 Ethernet-like frame.

    Fields:
    - destination_mac: MAC address of the next-hop receiver
    - source_mac: MAC address of the sender interface
    - ether_type: identifies the payload type, usually IPv4
    - payload: the Layer 3 IP packet
    """

    def __init__(self, destination_mac, source_mac, payload, ether_type=ETH_TYPE_IPV4):
        self.destination_mac = destination_mac
        self.source_mac = source_mac
        self.ether_type = ether_type
        self.payload = payload

    def __str__(self):
        return (
            f"EthernetFrame("
            f"SRC_MAC={self.source_mac}, "
            f"DST_MAC={self.destination_mac}, "
            f"TYPE={hex(self.ether_type)}"
            f")"
        )


class IPPacket:
    """
    Represents a Layer 3 IP-like packet.

    Fields:
    - source_ip: IP address of original sender
    - destination_ip: IP address of final receiver
    - ttl: Time To Live value, decreased by routers
    - protocol: identifies the Layer 4 protocol, usually UDP
    - total_length: size of IP header plus payload
    - payload: the Layer 4 UDP-like segment
    """

    IP_HEADER_SIZE = 20

    def __init__(self, source_ip, destination_ip, payload, ttl=4, protocol=IP_PROTOCOL_UDP):
        self.source_ip = source_ip
        self.destination_ip = destination_ip
        self.ttl = ttl
        self.protocol = protocol
        self.payload = payload
        self.total_length = self.IP_HEADER_SIZE + payload.length

    def decrement_ttl(self):
        """
        Decreases TTL by 1.

        Returns:
        - True if the packet is still valid
        - False if TTL has expired
        """
        self.ttl -= 1
        return self.ttl > 0

    def is_for_destination(self, ip_address):
        """
        Checks whether this packet is meant for the given IP address.
        """
        return self.destination_ip == ip_address

    def __str__(self):
        return (
            f"IPPacket("
            f"SRC_IP={self.source_ip}, "
            f"DST_IP={self.destination_ip}, "
            f"TTL={self.ttl}, "
            f"PROTOCOL={self.protocol}, "
            f"TOTAL_LENGTH={self.total_length}"
            f")"
        )


class UDPSegment:
    """
    Represents a Layer 4 UDP-like segment with ACK support.

    Fields:
    - source_port: sender application port
    - destination_port: receiver application port
    - length: transport header size plus data size
    - checksum: computed value used for simple error detection
    - segment_type: DATA or ACK
    - sequence_number: alternating bit number, either 0 or 1
    - data: application message data
    """

    UDP_HEADER_SIZE = 9

    def __init__(
        self,
        source_port,
        destination_port,
        data="",
        segment_type=DATA,
        sequence_number=0
    ):
        self.source_port = source_port
        self.destination_port = destination_port
        self.data = data
        self.segment_type = segment_type
        self.sequence_number = sequence_number
        self.length = self.UDP_HEADER_SIZE + len(self.data)
        self.checksum = self.compute_checksum()

    def compute_checksum(self):
        """
        Computes a simple checksum.

        This is not a real UDP checksum.
        It is a simple deterministic checksum suitable for this simulation.
        """
        checksum_data = (
            str(self.source_port)
            + str(self.destination_port)
            + str(self.length)
            + str(self.segment_type)
            + str(self.sequence_number)
            + self.data
        )

        total = 0

        for character in checksum_data:
            total += ord(character)

        return total % 65536

    def verify_checksum(self):
        """
        Verifies whether the current checksum matches the segment contents.
        """
        return self.checksum == self.compute_checksum()

    def is_data(self):
        """
        Returns True if this segment is a DATA segment.
        """
        return self.segment_type == DATA

    def is_ack(self):
        """
        Returns True if this segment is an ACK segment.
        """
        return self.segment_type == ACK

    def __str__(self):
        if self.segment_type == DATA:
            segment_name = "DATA"
        else:
            segment_name = "ACK"

        return (
            f"UDPSegment("
            f"TYPE={segment_name}, "
            f"SEQ={self.sequence_number}, "
            f"SRC_PORT={self.source_port}, "
            f"DST_PORT={self.destination_port}, "
            f"LENGTH={self.length}, "
            f"CHECKSUM={self.checksum}"
            f")"
        )


def create_data_segment(source_port, destination_port, data, sequence_number):
    """
    Creates a DATA transport segment.
    """
    return UDPSegment(
        source_port=source_port,
        destination_port=destination_port,
        data=data,
        segment_type=DATA,
        sequence_number=sequence_number
    )


def create_ack_segment(source_port, destination_port, sequence_number):
    """
    Creates an ACK transport segment.

    ACK segments contain no application data.
    """
    return UDPSegment(
        source_port=source_port,
        destination_port=destination_port,
        data="",
        segment_type=ACK,
        sequence_number=sequence_number
    )


def split_message_into_segments(message, maximum_data_size):
    """
    Splits a long application message into smaller chunks.

    The assignment limits each UDP-like segment to 500 bytes of data.
    This function returns a list of message chunks.
    """
    segments = []

    start_index = 0

    while start_index < len(message):
        end_index = start_index + maximum_data_size
        segment_data = message[start_index:end_index]
        segments.append(segment_data)
        start_index = end_index

    return segments
