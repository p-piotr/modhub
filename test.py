from networking import Networking
from socket import *
from select import select

dest_ip = '192.168.1.1'
dest_mac = '94:3C:96:7D:14:30'
source_ip = '192.168.1.35'
source_mac = '84:7B:57:47:04:DC'
packet = Networking.Layers.IPv4.UDP.DNS.create_dns_packet(dest_mac, dest_ip, 
            55555, 0x1234, 0x5678, 0x0100, [ { 'name' : '37.1.168.192.in-addr.arpa'} ], [], [], [ { 'name' : '<Root>' } ], source_mac=source_mac, source_ip=source_ip)

for byte in packet:
    print(hex(byte)[2:] + ' ', end='')
print('')

s = Networking.Sockets.get_sending_socket(interface='wlan0')
sr = Networking.Sockets.get_receiving_socket()
sent_bytes = s.send(packet)
print(f'Bytes sent: {sent_bytes}')
while True:
    ready = select([sr], [], [], 0.5)
    if ready[0]:
        packet = sr.recv(4096)
        if int.from_bytes(packet[36:38]) == 55555:
            dns_layer = Networking.Layers.IPv4.UDP.DNS.interpret_dns_layer(packet[42:])
            print(f'Response: \n{dns_layer}')
            break

#c = Networking.Convert.convert_hostname_to_dns_format('37.1.168.192.in-addr.arpa')
mdns = Networking.Layers.IPv4.UDP.DNS.create_dns_packet('01:00:5E:00:00:FB', 
                    '224.0.0.251', 5353, 0x1234, 0x5678, 0, 
                    [ { 'name' : '1.1.168.192.in-addr.arpa', 'type' : 12, 'class' : 1 } ], 
                    [], [], [ { 'name' : '<Root>', 'type' : 41 } ], 
                    source_mac='84:7B:57:47:04:DC', source_ip='192.168.1.35', 
                    destination_udp_port=5353, ttl=255)
s.send(mdns)
s.close()
sr.close()