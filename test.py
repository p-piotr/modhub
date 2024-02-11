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

data = Networking.Layers.IPv4.create_ipv4_layer(ips, True)
for byte in data:
    print(hex(byte)[2:] + ' ', end='')
print('')

ps2 = Networking.Layers.IPv4.interpret_ipv4_layer(data)
packet = Networking.Layers.Ethernet.ARP.create_arp_request_packet('192.168.1.35', source_mac='B2:95:75:09:BA:DC', source_ip='192.168.1.31')
for byte in packet:
    print(hex(byte)[2:] + ' ', end='')
print('')