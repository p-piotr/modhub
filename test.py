from networking import Networking

ips = Networking.Layers.IPv4.IPv4Struct()
ips.header_length = 5
ips.version = 4
ips.ecn = 0
ips.services = 0
ips.total_length = 118
ips.id = 21733
ips.flags = 2
ips.fragment_offset = 0
ips.ttl = 64
ips.protocol = 17
ips.checksum = 0x621d
ips.source_address = Networking.Convert.cubytearray(Networking.Convert.convert_ip_address('192.168.1.1'))
ips.destination_address = Networking.Convert.cubytearray(Networking.Convert.convert_ip_address('192.168.1.35'))

data = Networking.Layers.IPv4.create_ipv4_layer_from_struct(ips, True)
for byte in data:
    print(hex(byte)[2:] + ' ', end='')
print('')

ps2 = Networking.Layers.IPv4.interpret_ipv4_layer(data)
packet = Networking.Layers.Ethernet.ARP.create_arp_request_packet('192.168.1.35', source_mac='B2:95:75:09:BA:DC', source_ip='192.168.1.31')
for byte in packet:
    print(hex(byte)[2:] + ' ', end='')
print('')
udp_data = b'\xd8\x24\x85\x80\x00\x01\x00\x01\x00\x00\x00\x01\x02\x31\x39\x01\x31\x03\x31\x36\x38\x03\x31\x39\x32\x07\x69\x6e\x2d\x61\x64\x64\x72\x04\x61\x72\x70\x61\x00\x00\x0c\x00\x01\xc0\x0c\x00\x0c\x00\x01\x00\x00\x00\x00\x00\x18\x11\x64\x65\x73\x6b\x74\x6f\x70\x2d\x37\x65\x38\x6f\x6d\x65\x67\x2d\x31\x04\x68\x6f\x6d\x65\x00\x00\x00\x29\x10\x00\x00\x00\x00\x00\x00\x00'

udp = Networking.Layers.IPv4.UDP.create_udp_layer(source_port=53, destination_port=48807, udp_data=udp_data, 
                                                  source_ip='192.168.1.1', destination_ip='192.168.1.35')
if udp is not None:
    for byte in udp:
        print(hex(byte)[2:] + ' ', end='')
    print('')