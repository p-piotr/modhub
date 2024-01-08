from socket import *
import fcntl
import struct
import ctypes
from ctypes import c_uint8, c_uint16, c_uint32, c_ubyte
import globals

class Networking:
    SIOCGIFADDR = 0x8915
    SIOCGIFBRDADDR = 0x8919
    SIOCGIFNETMASK = 0x891B
    SIOCGIFHWADDR = 0x8927

    ETH_P_ALL = 3

    class Convert:
        def cubytearray(b):
            return (c_ubyte * len(b))(*bytearray(b))

    class IP:
        def get_ip_address(ifname='default', bytearr=True):
            if ifname == 'default':
                ifname = globals.GetDefaultInterface()
            with socket(AF_INET, SOCK_DGRAM) as s:
                try:
                    ip = fcntl.ioctl(
                        s.fileno(),
                        Networking.SIOCGIFADDR,
                        struct.pack('256s', ifname[:15].encode('utf-8'))
                    )[20:24]
                    if bytearr:
                        return bytearray(ip)
                    return inet_ntoa(ip)
                except OSError:
                    return 'null'
        
        def get_br_address(ifname='default', bytearr=True):
            if ifname == 'default':
                ifname = globals.GetDefaultInterface()
            with socket(AF_INET, SOCK_DGRAM) as s:
                try:
                    broadcast_ip = fcntl.ioctl(
                        s.fileno(),
                        Networking.SIOCGIFBRDADDR,
                        struct.pack('256s', ifname[:15].encode('utf-8'))
                    )[20:24]
                    if bytearr:
                        return bytearray(broadcast_ip)
                    return inet_ntoa(broadcast_ip)
                except OSError:
                    return 'null'
                
        def convert_ip_address(ip_address : str) -> bytearray:
            return bytearray(inet_aton(ip_address))

    class Mac:       
        def get_mac_address(ifname='default', bytearr=True):
            if ifname == 'default':
                ifname = globals.GetDefaultInterface()
            with socket(AF_INET, SOCK_DGRAM) as s:
                try:
                    mac = fcntl.ioctl(
                        s.fileno(),
                        Networking.SIOCGIFHWADDR,
                        struct.pack('256s', ifname[:15].encode('utf-8'))
                    )[18:24]
                    if bytearr:
                        return bytearray(mac)
                    return ''.join(':{:02X}'.format(b) for b in mac).lstrip(':')
                except OSError:
                    return 'null'
        
        def convert_mac_address(mac_address : str) -> bytearray:
            return bytearray(bytes.fromhex(mac_address.replace(':', '')))

    class Interfaces:
        def get_network_interfaces() -> list:
            if_ni = if_nameindex()
            ifaces = list()
            for iface in enumerate(if_ni):
                ifaces.append(iface[1][1])
            return ifaces
        
        def get_network_gateway(iface : str, bytearr=True):
            with open('/proc/net/route') as f:
                for line in f:
                    fields = line.strip().split()
                    if fields[0] != iface or fields[1] != '00000000' or not int(fields[3], 16) & 2:
                        continue
                    if bytearr:
                        return bytearray(struct.pack('<L', int(fields[2], 16)))
                    else:
                        return inet_ntoa(struct.pack('<L', int(fields[2], 16)))
                return 'None'
        
    class Layers:
        class Ethernet:
            class EthernetStruct(ctypes.BigEndianStructure):
                _fields_ = [
                    ('destination_mac', c_uint8 * 6),
                    ('source_mac', c_uint8 * 6),
                    ('type', c_uint16)
                ]

            def create_ethernet_header(es : EthernetStruct) -> bytes:
                return bytes(ctypes.string_at(ctypes.addressof(es), ctypes.sizeof(es)))
            
            def interpret_ethernet_header(ethernet_header : bytes) -> EthernetStruct:
                return Networking.Layers.Ethernet.EthernetStruct.from_buffer_copy(ethernet_header)
            
            class ARP:
                class ARPStruct(ctypes.BigEndianStructure):
                    _fields_ = [
                        ('hardware_type', c_uint16),
                        ('protocol_type', c_uint16),
                        ('hardware_size', c_uint8),
                        ('protocol_size', c_uint8),
                        ('opcode', c_uint16),
                        ('sender_mac_address', c_uint8 * 6),
                        ('sender_ip_address', c_uint8 * 4),
                        ('target_mac_address', c_uint8 * 6),
                        ('target_ip_address', c_uint8 * 4)
                    ]
                
                def create_arp_header(arp : ARPStruct) -> bytes:
                    return bytes(ctypes.string_at(ctypes.addressof(arp), ctypes.sizeof(arp)))
                
                def interpret_arp_header(arp_header : bytes) -> ARPStruct:
                    return Networking.Layers.Ethernet.ARP.ARPStruct.from_buffer_copy(arp_header)
                
                def create_arp_request_header(target_ip : str, source_mac='default', source_ip='default') -> bytes:
                    if source_mac == 'default':
                        source_mac = Networking.Mac.get_mac_address()
                    if source_ip == 'default':
                        source_ip = Networking.IP.get_ip_address()

                    if type(source_mac) != bytearray:
                        source_mac = Networking.Mac.convert_mac_address(source_mac)
                    if type(source_ip) != bytearray:
                        source_ip = Networking.IP.convert_ip_address(source_ip)
                    if type(target_ip) != bytearray:
                        target_ip = Networking.IP.convert_ip_address(target_ip)
                    source_mac = Networking.Convert.cubytearray(source_mac)
                    source_ip = Networking.Convert.cubytearray(source_ip)
                    target_ip = Networking.Convert.cubytearray(target_ip)
                    eth = Networking.Layers.Ethernet.EthernetStruct()
                    arp = Networking.Layers.Ethernet.ARP.ARPStruct()
                    eth.destination_mac = Networking.Convert.cubytearray(Networking.Mac.convert_mac_address('FF:FF:FF:FF:FF:FF'))
                    eth.source_mac = source_mac
                    eth.type = 0x0806
                    arp.hardware_type = 1
                    arp.protocol_type = 0x0800
                    arp.hardware_size = 6
                    arp.protocol_size = 4
                    arp.opcode = 1
                    arp.sender_mac_address = source_mac
                    arp.sender_ip_address = source_ip
                    arp.target_mac_address = Networking.Convert.cubytearray(Networking.Mac.convert_mac_address('00:00:00:00:00:00'))
                    arp.target_ip_address = target_ip
                    return Networking.Layers.Ethernet.create_ethernet_header(eth) + Networking.Layers.Ethernet.ARP.create_arp_header(arp)
                
                def create_arp_reply_header(source_mac, source_ip, target_mac, target_ip):
                    if type(source_mac) != bytearray:
                        source_mac = Networking.Mac.convert_mac_address(source_mac)
                    if type(target_mac) != bytearray:
                        target_mac = Networking.Mac.convert_mac_address(target_mac)
                    if type(source_ip) != bytearray:
                        source_ip = Networking.IP.convert_ip_address(source_ip)
                    if type(target_ip) != bytearray:
                        target_ip = Networking.IP.convert_ip_address(target_ip)
                    source_mac = Networking.Convert.cubytearray(source_mac)
                    target_mac = Networking.Convert.cubytearray(target_mac)
                    source_ip = Networking.Convert.cubytearray(source_ip)
                    target_ip = Networking.Convert.cubytearray(target_ip)
                    eth = Networking.Layers.Ethernet.EthernetStruct()
                    arp = Networking.Layers.Ethernet.ARP.ARPStruct()
                    eth.destination_mac = target_mac
                    eth.source_mac = source_mac
                    eth.type = 0x0806
                    arp.hardware_type = 1
                    arp.protocol_type = 0x0800
                    arp.hardware_size = 6
                    arp.protocol_size = 4
                    arp.opcode = 2
                    arp.sender_mac_address = source_mac
                    arp.sender_ip_address = source_ip
                    arp.target_mac_address = target_mac
                    arp.target_ip_address = target_ip
                    return Networking.Layers.Ethernet.create_ethernet_header(eth) + Networking.Layers.Ethernet.ARP.create_arp_header(arp)

            class IPv4:
                class IPv4Struct(ctypes.LittleEndianStructure):
                    _fields_ = [
                        ('version', c_uint32, 4),
                        ('header_length', c_uint32, 4),
                        ('services', c_uint32, 6),
                        ('ecn', c_uint32, 2),
                        ('total_length', c_uint16),
                        ('id', c_uint16),
                        ('flags', c_uint32, 3),
                        ('fragment_offset', c_uint32, 13),
                        ('ttl', c_uint8),
                        ('protocol', c_uint8),
                        ('checksum', c_uint16),
                        ('source_address', c_uint8 * 4),
                        ('destination_address', c_uint8 * 4)
                    ]

                def create_ipv4_layer(ips : IPv4Struct) -> bytes:
                    return bytes(ctypes.string_at(ctypes.addressof(ips), ctypes.sizeof(ips)))

                def interpret_ipv4_layer(ipv4_layer : bytes) -> IPv4Struct:
                    return Networking.Layers.Ethernet.IPv4.IPv4Struct.from_buffer_copy(ipv4_layer)

                class UDP:
                    class UDPStruct(ctypes.LittleEndianStructure):
                        _fields_ = [
                            ('source_port', c_uint16),
                            ('destination_port', c_uint16),
                            ('length', c_uint16),
                            ('checksum', c_uint16)
                        ]

                    def create_udp_layer(udps : UDPStruct) -> bytes:
                        return bytes(ctypes.string_at(ctypes.addressof(udps), ctypes.sizeof(udps)))

                    def interpret_udp_layer(udp_layer : bytes) -> UDPStruct:
                        return Networking.Layers.Ethernet.IPv4.UDP.UDPStruct.from_buffer_copy(udp_layer)

                    class DNS:
                        #class DNSStruct(ctypes.LittleEndianStructure):
                        #    _fields_ = [
                        #        ('id', c_uint16),
                        #        ('flags', c_uint16),
                        #        ('questions', c_uint16),
                        #        ('answer_rrs', c_uint16),
                        #        ('authority_rrs', c_uint16),
                        #        ('additional_rrs', c_uint16),
                        #        ()
                        #    ]
                        def interpret_dns_header(dns_header : bytes) -> dict:
                            transaction_id = int.from_bytes(dns_header[0:2], 'big')
                            flags = int.from_bytes(dns_header[2:4], 'big')
                            questions = int.from_bytes(dns_header[4:6], 'big')
                            answer_rrs = int.from_bytes(dns_header[6:8], 'big')
                            authority_rrs = int.from_bytes(dns_header[8:10], 'big')
                            additional_rrs = int.from_bytes(dns_header[10:12], 'big')
                            queries = list()
                            answers = list()
                            # authority_records = list()
                            additional_records = list()
                            j = 12
                            for i in range(questions):
                                k = dns_header.find(b'\x00', j)
                                name = dns_header[j:k]
                                j = k + 1
                                type = int.from_bytes(dns_header[j:j+2], 'big')
                                q_class = int.from_bytes(dns_header[j+2:j+4], 'big')
                                j += 4
                                queries.append({
                                    'name' : name,
                                    'type' : type,
                                    'class' : q_class
                                })
                            for i in range(answer_rrs):
                                name = dns_header[j:j+2]
                                type = int.from_bytes(dns_header[j+2:j+4], 'big')
                                q_class = int.from_bytes(dns_header[j+4:j+6], 'big')
                                ttl = int.from_bytes(dns_header[j+6:j+10], 'big')
                                data_len = int.from_bytes(dns_header[j+10:j+12], 'big')
                                j += 12
                                k = dns_header.find(b'\x00', j)
                                domain_name = dns_header[j:k]
                                j = k + 1
                                answers.append({
                                    'name' : name,
                                    'type' : type,
                                    'class' : q_class,
                                    'ttl' : ttl,
                                    'data_len' : data_len,
                                    'domain_name' : domain_name
                                })
                            for i in range(additional_rrs):
                                name = int.from_bytes(dns_header[j:j+1], 'big')
                                type = int.from_bytes(dns_header[j+1:j+3], 'big')
                                udp_payload_size = int.from_bytes(dns_header[j+3:j+5], 'big')
                                hb_rcode = int.from_bytes(dns_header[j+5:j+6], 'big')
                                edns0 = int.from_bytes(dns_header[j+6:j+7], 'big')
                                z = int.from_bytes(dns_header[j+7:j+9], 'big')
                                data_len = int.from_bytes(dns_header[j+9:j+11], 'big')
                                additional_records.append({
                                    'name' : name,
                                    'type' : type,
                                    'udp_payload_size' : udp_payload_size,
                                    'hb_rcode' : hb_rcode,
                                    'edns0' : edns0,
                                    'z' : z,
                                    'data_len' : data_len
                                })
                            return {
                                'transaction_id' : transaction_id,
                                'flags' : flags,
                                'questions' : questions,
                                'answer_rrs' : answer_rrs,
                                'authority_rrs' : authority_rrs,
                                'additional_rrs' : additional_rrs,
                                'queries' : queries,
                                'answers' : answers,
                                # 'authority_records' : authority_records,
                                'additional_records' : additional_records
                            }
                        
    class Sockets:
        def get_receiving_socket():
            return socket(AF_PACKET, SOCK_RAW, htons(Networking.ETH_P_ALL))
        
        def get_sending_socket():
            s = socket(AF_PACKET, SOCK_RAW, IPPROTO_RAW)
            s.bind((globals.variables['iface'], 0))
            return s
        
        def initialize_sockets():
            globals.sockets.clear()
            #globals.sockets['send'] = Networking.Sockets.get_sending_socket()
            #globals.sockets['recv'] = Networking.Sockets.get_receiving_socket()
        
        def close_sockets():
            for s in globals.sockets.values():
                s.close()