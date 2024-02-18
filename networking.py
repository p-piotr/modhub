from socket import *
import fcntl
import struct
import ctypes
from ctypes import c_uint8, c_uint16, c_uint32, c_ubyte
from select import select
import globals
import random
from binary_operations import binary_not

class Networking:
    SIOCGIFADDR = 0x8915        # get interface ip address
    SIOCGIFBRDADDR = 0x8919     # get interface broadcast ip address
    SIOCGIFNETMASK = 0x891B     # get interface netmask
    SIOCGIFHWADDR = 0x8927      # get interface mac address
    SIOCGIWNAME = 0x8B15        # get access point mac address
    SIOCGIWESSID = 0x8B1B       # get network name

    ETH_P_ALL = 3

    class Convert:
        def cubytearray(b):
            return (c_ubyte * len(b))(*bytearray(b))

        def convert_ip_address(ip_address : str | bytes) -> str | bytes:
            if type(ip_address) == str:
                return inet_aton(ip_address)
            return inet_ntoa(ip_address)

        def convert_mac_address(mac_address : str | bytes) -> str | bytes:
            if type(mac_address) == str:
                return bytes.fromhex(mac_address.replace(':', ''))
            return ''.join(':{:02X}'.format(b) for b in mac_address).lstrip(':')
        
        def convert_hostname_to_dns_format(hostname : str) -> bytes:
            fullstop_indices = [pos for pos, char in enumerate(hostname) if char == '.']
            hostname = bytearray(hostname.encode('utf-8'))
            for i in range(0, len(fullstop_indices) - 1):
                hostname[fullstop_indices[i]] = fullstop_indices[i + 1] - fullstop_indices[i] - 1
            hostname[fullstop_indices[len(fullstop_indices) - 1]] = len(hostname) - fullstop_indices[len(fullstop_indices) - 1] - 1
            hostname = fullstop_indices[0].to_bytes(1, 'big') + hostname + b'\x00'
            return bytes(hostname)
        
        def convert_hostname_from_dns_format(hostname_dns : bytes) -> str:
            hostname_dns = bytearray(hostname_dns)
            i = 0
            while True:
                j = int(hostname_dns[i])
                if j == 0:
                    break
                elif i > 0:
                    hostname_dns[i] = ord('.')
                i += j + 1
            return hostname_dns[1:-1].decode('utf-8')

        def convert_ip_from_reverse_dns_form(ip : bytes, return_bytes=True) -> str | bytes:
            ip = ip[:-13]
            l = ip.split('.')
            ret_addr = ''
            for p in reversed(l):
                ret_addr += p + '.'
            ret_addr = ret_addr[:-1]
            if return_bytes:
                return 
        def get_hostname_by_ip(ss : socket, sr : socket, host : bytes, return_bytes=True) -> str | bytes:
            rand16 = lambda : random.randint(0, 0xFFFF)
            host = convert_ip_to_reverse_dns_form(host, return_bytes=False)
            port = random.randint(18000, 59500)
            dns_transaction_id = rand16()
            gateway_ip = Networking.IP.get_gateway_ip_address()
            gateway_mac = Networking.Mac.get_gateway_mac_address()
            packet = Networking.Layers.IPv4.UDP.DNS.create_dns_packet(gateway_mac, gateway_ip, port, rand16(), 
                                        dns_transaction_id, 0x0100, [ { 'name' : host } ], [], [], [ { 'name' : '<Root>' } ])
            ss.send(packet)
            while True:
                ready = select([sr], [], [], 0.5)
                if ready[0]:
                    answer = sr.recv(4096)
                    ip = Networking.Layers.IPv4.interpret_ipv4_layer(answer[14:34])
                    if bytes(ip.source_address) == gateway_ip:
                        udp = Networking.Layers.IPv4.UDP.interpret_udp_layer(answer[34:42])
                        if udp.destination_port == port:
                            dns = Networking.Layers.IPv4.UDP.DNS.interpret_dns_layer(answer[42:])
                            domain_name = dns['answers'][0]['domain_name']
                            if return_bytes:
                                return domain_name.encode()
                            return domain_name

            class IP:
        def get_ip_address(interface='default', return_bytes=True):
            if interface == 'default':
                interface = globals.GetDefaultInterface()
            with socket(AF_INET, SOCK_DGRAM) as s:
                try:
                    ip = fcntl.ioctl(
                        s.fileno(),
                        Networking.SIOCGIFADDR,
                        struct.pack('256s', interface[:15].encode('utf-8'))
                    )[20:24]
                    if return_bytes:
                        return ip
                    return inet_ntoa(ip)
                except OSError:
                    return None
                
        def get_ip_address_ipv6(interface='default', return_bytes=True):
            if interface == 'default':
                interface = globals.GetDefaultInterface()
            with open('/proc/net/if_inet6') as f:
                for line in f:
                    fields = line.strip().split()
                    if fields[5] != interface:
                        continue
                    ip = bytes.fromhex(fields[0])
                    if return_bytes:
                        return ip
                    return inet_ntop(AF_INET6, ip)
            return None
        
        def get_br_address(interface='default', return_bytes=True):
            if interface == 'default':
                interface = globals.GetDefaultInterface()
            with socket(AF_INET, SOCK_DGRAM) as s:
                try:
                    broadcast_ip = fcntl.ioctl(
                        s.fileno(),
                        Networking.SIOCGIFBRDADDR,
                        struct.pack('256s', interface[:15].encode('utf-8'))
                    )[20:24]
                    if return_bytes:
                        return broadcast_ip
                    return inet_ntoa(broadcast_ip)
                except OSError:
                    return None

        def get_gateway_ip_address(interface='default', return_bytes=True) -> bytes | str:
            if interface == 'default':
                interface = globals.GetDefaultInterface()
            with open('/proc/net/route') as f:
                for line in f:
                    fields = line.strip().split()
                    if fields[0] != interface or fields[1] != '00000000' or not int(fields[3], 16) & 2:
                        continue
                    if return_bytes:
                        return struct.pack('<L', int(fields[2], 16))
                    else:
                        return inet_ntoa(struct.pack('<L', int(fields[2], 16)))
            return None
            
        def get_network_mask(interface='default', return_bytes=True) -> bytes | str:
            if interface == 'default':
                interface = globals.GetDefaultInterface()
            with socket(AF_INET, SOCK_DGRAM) as s:
                s.setsockopt(SOL_SOCKET, SO_BINDTODEVICE, str(interface + '\0').encode('utf-8'))
                try:
                    mask = fcntl.ioctl(
                        s.fileno(),
                        Networking.SIOCGIFNETMASK,
                        struct.pack('256s', interface[:15].encode('utf-8'))
                    )[20:24]
                    if return_bytes:
                        return mask
                    return inet_ntoa(mask)
                except OSError:
                    return None

    class Mac:       
        def get_mac_address(interface='default', return_bytes=True):
            if interface == 'default':
                interface = globals.GetDefaultInterface()
            with socket(AF_INET, SOCK_DGRAM) as s:
                try:
                    mac = fcntl.ioctl(
                        s.fileno(),
                        Networking.SIOCGIFHWADDR,
                        struct.pack('256s', interface[:15].encode('utf-8'))
                    )[18:24]
                    if return_bytes:
                        return mac
                    return Networking.Convert.convert_mac_address(mac)
                except OSError:
                    return None

        def get_gateway_mac_address(interface='default', return_bytes=True):
            if interface == 'default':
                interface = globals.GetDefaultInterface()
            with socket(AF_INET, SOCK_DGRAM) as s:
                try:
                    mac = fcntl.ioctl(
                        s.fileno(),
                        Networking.SIOCGIWNAME,
                        struct.pack('256s', interface[:15].encode('utf-8'))
                    )[18:24]
                    if return_bytes:
                        return mac
                    return Networking.Convert.convert_mac_address(mac)
                except OSError:
                    return None

    class Interfaces:
        def get_network_interfaces() -> list:
            if_ni = if_nameindex()
            interfaces = list()
            for interface in enumerate(if_ni):
                interfaces.append(interface[1][1])
            return interfaces
        
    class Layers:
        class Ethernet:
            class EthernetStruct(ctypes.BigEndianStructure):
                _fields_ = [
                    ('destination_mac', c_uint8 * 6),
                    ('source_mac', c_uint8 * 6),
                    ('type', c_uint16)
                ]
            
            def create_ethernet_layer(destination_mac, eth_type, source_mac='default') -> bytes:
                if source_mac == 'default':
                    source_mac = Networking.Mac.get_mac_address()
                if type(source_mac) != bytes:
                    source_mac = Networking.Convert.convert_mac_address(source_mac)
                if type(destination_mac) != bytes:
                    destination_mac = Networking.Convert.convert_mac_address(destination_mac)
                eth = Networking.Layers.Ethernet.EthernetStruct()
                eth.destination_mac = Networking.Convert.cubytearray(destination_mac)
                eth.source_mac = Networking.Convert.cubytearray(source_mac)
                eth.type = eth_type
                return Networking.Layers.Ethernet.create_ethernet_layer_from_struct(eth)

            def create_ethernet_layer_from_struct(es : EthernetStruct) -> bytes:
                return ctypes.string_at(ctypes.addressof(es), ctypes.sizeof(es))
            
            def interpret_ethernet_layer(ethernet_header : bytes) -> EthernetStruct:
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
                        ('destination_mac_address', c_uint8 * 6),
                        ('destination_ip_address', c_uint8 * 4)
                    ]
                
                def create_arp_layer(destination_mac, destination_ip, opcode, source_mac='default', 
                                     source_ip='default', hardware_type=1, protocol_type=0x0800, hardware_size=6, protocol_size=4) -> bytes:
                    if source_mac == 'default':
                        source_mac = Networking.Mac.get_mac_address()
                    if source_ip == 'default':
                        source_ip = Networking.IP.get_ip_address()
                    if type(source_mac) != bytes:
                        source_mac = Networking.Convert.convert_mac_address(source_mac)
                    if type(source_ip) != bytes:
                        source_ip = Networking.Convert.convert_ip_address(source_ip)
                    if type(destination_mac) != bytes:
                        destination_mac = Networking.Convert.convert_mac_address(destination_mac)
                    if type(destination_ip) != bytes:
                        destination_ip = Networking.Convert.convert_ip_address(destination_ip)
                    arp = Networking.Layers.Ethernet.ARP.ARPStruct()
                    arp.hardware_type = hardware_type
                    arp.protocol_type = protocol_type
                    arp.hardware_size = hardware_size
                    arp.protocol_size = protocol_size
                    arp.opcode = opcode
                    arp.sender_mac_address = Networking.Convert.cubytearray(source_mac)
                    arp.sender_ip_address = Networking.Convert.cubytearray(source_ip)
                    arp.destination_mac_address = Networking.Convert.cubytearray(destination_mac)
                    arp.destination_ip_address = Networking.Convert.cubytearray(destination_ip)
                    return Networking.Layers.Ethernet.ARP.create_arp_layer_from_struct(arp)

                def create_arp_layer_from_struct(arp : ARPStruct) -> bytes:
                    return ctypes.string_at(ctypes.addressof(arp), ctypes.sizeof(arp))
                
                def interpret_arp_layer(arp_header : bytes) -> ARPStruct:
                    return Networking.Layers.Ethernet.ARP.ARPStruct.from_buffer_copy(arp_header)
                
                def create_arp_request_packet(destination_ip, source_mac='default', source_ip='default') -> bytes:
                    eth_bytes = Networking.Layers.Ethernet.create_ethernet_layer('FF:FF:FF:FF:FF:FF', 0x0806, source_mac=source_mac)
                    arp_bytes = Networking.Layers.Ethernet.ARP.create_arp_layer('00:00:00:00:00:00', 
                                                                                destination_ip, 1, source_mac=source_mac, source_ip=source_ip)
                    return eth_bytes + arp_bytes
                
                def create_arp_reply_packet(destination_mac, destination_ip, source_mac='default', source_ip='default'):
                    eth_bytes = Networking.Layers.Ethernet.create_ethernet_layer(destination_mac, 0x0806, source_mac=source_mac)
                    arp_bytes = Networking.Layers.Ethernet.ARP.create_arp_layer(destination_mac, 
                                                                                destination_ip, 2, source_mac=source_mac, source_ip=source_ip)
                    return eth_bytes + arp_bytes

        class IPv4:
            class IPv4Struct(ctypes.BigEndianStructure):
                _fields_ = [
                    ('version', c_uint8, 4),
                    ('header_length', c_uint8, 4),
                    ('services', c_uint8, 6),
                    ('ecn', c_uint8, 2),
                    ('total_length', c_uint16),
                    ('id', c_uint16),
                    ('flags', c_uint16, 3),
                    ('fragment_offset', c_uint16, 13),
                    ('ttl', c_uint8),
                    ('protocol', c_uint8),
                    ('checksum', c_uint16),
                    ('source_address', c_uint8 * 4),
                    ('destination_address', c_uint8 * 4)
                ]

            def create_ipv4_layer(total_length, id, protocol, destination_address, 
                                  version=4, header_length=5, services=0, ecn=0, flags=2, 
                                  fragment_offset=0, ttl=64, checksum=0, source_address='default', calculate_checksum=True) -> bytes:
                if source_address == 'default':
                    source_address = Networking.IP.get_ip_address()
                if type(source_address) != bytes:
                    source_address = Networking.Convert.convert_ip_address(source_address)
                if type(destination_address) != bytes:
                    destination_address = Networking.Convert.convert_ip_address(destination_address)
                ips = Networking.Layers.IPv4.IPv4Struct()
                ips.version = version
                ips.header_length = header_length
                ips.services = services
                ips.ecn = ecn
                ips.total_length = total_length
                ips.id = id
                ips.flags = flags
                ips.fragment_offset = fragment_offset
                ips.ttl = ttl
                ips.protocol = protocol
                ips.source_address = Networking.Convert.cubytearray(source_address)
                ips.destination_address = Networking.Convert.cubytearray(destination_address)
                if calculate_checksum:
                    checksum = Networking.Layers.IPv4.calculate_ipv4_checksum(ips)
                ips.checksum = checksum
                return Networking.Layers.IPv4.create_ipv4_layer_from_struct(ips)

            def create_ipv4_layer_from_struct(ips : IPv4Struct, calculate_checksum=True) -> bytes:
                if calculate_checksum:
                    ips.checksum = Networking.Layers.IPv4.calculate_ipv4_checksum(ips)
                return ctypes.string_at(ctypes.addressof(ips), ctypes.sizeof(ips))

            def interpret_ipv4_layer(ipv4_layer : bytes) -> IPv4Struct:
                ips = Networking.Layers.IPv4.IPv4Struct.from_buffer_copy(ipv4_layer)
                return ips
            
            def calculate_ipv4_checksum(ips : IPv4Struct) -> int:
                data = ctypes.string_at(ctypes.addressof(ips), ctypes.sizeof(ips))
                sum = 0
                for i in range(0, ctypes.sizeof(ips), 2):
                    if i == 10:
                        continue # checksum field
                    word = int.from_bytes(data[i:i+2], 'big')
                    sum += word
                while sum > 0xFFFF:
                    overflow = sum // 0x10000
                    sum = sum % 0x10000
                    sum += overflow
                checksum = binary_not(sum, 16)
                if checksum == 0:
                    checksum = 0xFFFF
                return checksum

            class UDP:
                class UDPStruct(ctypes.BigEndianStructure):
                    _fields_ = [
                        ('source_port', c_uint16),
                        ('destination_port', c_uint16),
                        ('length', c_uint16),
                        ('checksum', c_uint16)
                    ]
                class UDPChecksumPseudoHeaderHelper:
                    def __init__(self, source_ip : str | bytes, destination_ip : str | bytes, data : bytes):
                        if type(source_ip) != bytes:
                            source_ip = Networking.Convert.convert_ip_address(source_ip)
                        if type(destination_ip) != bytes:
                            destination_ip = Networking.Convert.convert_ip_address(destination_ip)
                        self.source_ip = source_ip
                        self.destination_ip = destination_ip
                        self.data = data

                def create_udp_layer(source_port, destination_port, udp_data=None, source_ip=None, 
                                     destination_ip=None, length=0, checksum=0, calculate_length=True) -> bytes:
                    calculate_checksum = (source_ip is not None and destination_ip is not None and udp_data is not None)
                    if calculate_length and udp_data is None:
                        calculate_length = False
                    udps = Networking.Layers.IPv4.UDP.UDPStruct()
                    udps.source_port = source_port
                    udps.destination_port = destination_port
                    if calculate_length:
                        length = 8 + len(udp_data)
                    udps.length = length
                    if calculate_checksum:
                        udph = Networking.Layers.IPv4.UDP.UDPChecksumPseudoHeaderHelper(source_ip, destination_ip, udp_data)
                        checksum = Networking.Layers.IPv4.UDP.calculate_udp_checksum(udps, udph)
                    udps.checksum = checksum
                    return Networking.Layers.IPv4.UDP.create_udp_layer_from_struct(udps)

                def create_udp_layer_from_struct(udps : UDPStruct) -> bytes:
                    return ctypes.string_at(ctypes.addressof(udps), ctypes.sizeof(udps))

                def interpret_udp_layer(udp_layer : bytes) -> UDPStruct:
                    udps = Networking.Layers.IPv4.UDP.UDPStruct.from_buffer_copy(udp_layer)
                    return udps
                
                def calculate_udp_checksum(udps : UDPStruct, udph : UDPChecksumPseudoHeaderHelper) -> int:
                    itob = lambda x : int.to_bytes(x, 2, 'big')
                    sum = 0
                    for element in [ udph.source_ip, udph.destination_ip, itob(udps.length), 
                                    itob(udps.source_port), itob(udps.destination_port), itob(udps.length), udph.data ]:
                        for i in range(0, len(element), 2):
                            word = int.from_bytes(element[i:i+2], 'big')
                            sum += word
                    sum += 0x11 # UDP protocol
                    while sum > 0xFFFF:
                        overflow = sum // 0x10000
                        sum = sum % 0x10000
                        sum += overflow
                    checksum = binary_not(sum, 16)
                    if checksum == 0:
                        checksum = 0xFFFF
                    return checksum

                class DNS:
                    def get_dns_hostname_from_index(data : bytes, i : int) -> [bytes, int]:
                        if data[i] == 192: # '\xc0'
                            offset = data[i + 1]
                            return [ Networking.Layers.IPv4.UDP.DNS.get_dns_hostname_from_index(data, offset)[0], 2 ]
                        elif data[i] == 0:
                            return [ bytes(b''), 1 ]
                        current_part_len = data[i]
                        current_part = bytearray(data[i + 1 : i + current_part_len + 1])
                        next_part, next_part_len = Networking.Layers.IPv4.UDP.DNS.get_dns_hostname_from_index(data, i + current_part_len + 1)
                        next_part = bytearray(next_part)
                        if next_part == b'':
                            return [ bytes(current_part), current_part_len + next_part_len + 1 ]
                        return [ bytes(current_part + b'.' + next_part), current_part_len + next_part_len + 1 ]

                    def interpret_dns_layer(dns_header : bytes) -> dict:
                        transaction_id = int.from_bytes(dns_header[0:2], 'big')
                        flags = int.from_bytes(dns_header[2:4], 'big')
                        questions = int.from_bytes(dns_header[4:6], 'big')
                        answer_rrs = int.from_bytes(dns_header[6:8], 'big')
                        authority_rrs = int.from_bytes(dns_header[8:10], 'big')
                        additional_rrs = int.from_bytes(dns_header[10:12], 'big')
                        queries = list()
                        answers = list()
                        # TODO authority_records = list()
                        additional_records = list()
                        j = 12
                        for i in range(questions):
                            k = dns_header.find(b'\x00', j)
                            name = dns_header[j:k+1]
                            name = Networking.Convert.convert_hostname_from_dns_format(name)
                            j = k + 1
                            dns_type = int.from_bytes(dns_header[j:j+2], 'big')
                            q_class = int.from_bytes(dns_header[j+2:j+4], 'big')
                            j += 4
                            queries.append({
                                'name' : name,
                                'type' : dns_type,
                                'class' : q_class
                            })
                        for i in range(answer_rrs):
                            name, k = Networking.Layers.IPv4.UDP.DNS.get_dns_hostname_from_index(dns_header, j)
                            name = name.decode('utf-8')
                            dns_type = int.from_bytes(dns_header[j+k:j+k+2], 'big')
                            q_class = int.from_bytes(dns_header[j+k+2:j+k+4], 'big')
                            ttl = int.from_bytes(dns_header[j+k+4:j+k+8], 'big')
                            data_len = int.from_bytes(dns_header[j+k+8:j+k+10], 'big')
                            j += k + 10
                            domain_name, k = Networking.Layers.IPv4.UDP.DNS.get_dns_hostname_from_index(dns_header, j)
                            domain_name = domain_name.decode('utf-8')
                            j += k
                            answers.append({
                                'name' : name,
                                'type' : dns_type,
                                'class' : q_class,
                                'ttl' : ttl,
                                'data_len' : data_len,
                                'domain_name' : domain_name
                            })
                        for i in range(additional_rrs):
                            name, k = Networking.Layers.IPv4.UDP.DNS.get_dns_hostname_from_index(dns_header, j)
                            if name == b'':
                                name = b'<Root>'
                            name = name.decode('utf-8')
                            dns_type = int.from_bytes(dns_header[j+k:j+k+2], 'big')
                            udp_payload_size = int.from_bytes(dns_header[j+k+2:j+k+4], 'big')
                            hb_rcode = int.from_bytes(dns_header[j+k+4:j+k+5], 'big')
                            edns0 = int.from_bytes(dns_header[j+k+5:j+k+6], 'big')
                            z = int.from_bytes(dns_header[j+k+6:j+k+8], 'big')
                            data_len = int.from_bytes(dns_header[j+k+8:j+k+10], 'big')
                            additional_records.append({
                                'name' : name,
                                'type' : dns_type,
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
                            # TODO 'authority_records' : authority_records,
                            'additional_records' : additional_records
                        }
                        
                    def create_dns_layer(transaction_id, flags, questions, answer_rrs, authority_rrs, additional_rrs, queries, answers, authority_records, additional_records) -> bytes:
                        ht = lambda a : bytes(c_uint16(htons(a)))
                        transaction_id = ht(transaction_id)
                        flags = ht(flags)
                        questions = ht(questions)
                        answer_rrs = ht(answer_rrs)
                        authority_rrs = ht(authority_rrs)
                        additional_rrs = ht(additional_rrs)
                        queries_bytes = b''
                        answers_bytes = b''
                        additional_records_bytes = b''
                        hostname_indices = {}
                        for query in queries:
                            keys = query.keys()
                            if 'name' not in keys:
                                return None
                            hostname_indices[query['name']] = len(queries_bytes) + 12
                            queries_bytes += Networking.Convert.convert_hostname_to_dns_format(query['name'])
                            if 'type' in keys:
                                queries_bytes += ht(query['type'])
                            else:
                                queries_bytes += ht(12) # default type (PTR)
                            if 'class' in keys:
                                queries_bytes += ht(query['class'])
                            else:
                                queries_bytes += ht(1) # default class (IN)
                        for answer in answers:
                            keys = answer.keys()
                            if 'name' not in keys:
                                return None
                            if answer['name'] in hostname_indices:
                                answers_bytes += b'\xc0' + int.to_bytes(hostname_indices[answer['name']])
                            else:
                                answers_bytes += Networking.Convert.convert_hostname_to_dns_format(answer['name'])
                            if 'type' in keys:
                                answers_bytes += ht(answer['type'])
                            else:
                                answers_bytes += ht(12) # default type (PTR)
                            if 'class' in keys:
                                answers_bytes += ht(answer['class'])
                            else:
                                answers_bytes += ht(1) # default class (IN)
                            if 'ttl' in keys:
                                answers_bytes += answer['ttl'].to_bytes(4, 'big')
                            else:
                                answers_bytes += b'\x00\x00\x00\x00' # default ttl (0)
                            if 'domain_name' in keys:
                                domain_bytes = Networking.Convert.convert_hostname_to_dns_format(answer['domain_name'])
                                if 'data_len' in keys:
                                    answers_bytes += ht(answer['data_len'])
                                else:
                                    answers_bytes += ht(len(domain_bytes))
                                answers_bytes += domain_bytes
                            elif 'data_len' not in keys or answer['data_len'] == 0:
                                answers_bytes += b'\x00\x00'
                            else:
                                return None
                        for additional_record in additional_records:
                            keys = additional_record.keys()
                            if 'name' not in keys:
                                return None
                            if additional_record['name'] in hostname_indices:
                                additional_records_bytes += b'\xc0' + int.to_bytes(hostname_indices[answer['name']])
                            elif additional_record['name'] == '<Root>':
                                additional_records_bytes += b'\x00'
                            else:
                                additional_records_bytes += Networking.Convert.convert_hostname_to_dns_format(answer['name'])
                            if 'type' in keys:
                                additional_records_bytes += ht(additional_record['type'])
                            else:
                                additional_records_bytes += ht(41) # default type (OPT)
                            if 'udp_payload_size' in keys:
                                additional_records_bytes += ht(additional_record['udp_payload_size'])
                            else:
                                additional_records_bytes += ht(4096) # default udp payload size (4096)
                            if 'hb_rcode' in keys:
                                additional_records_bytes += int.to_bytes(additional_record['hb_rcode'])
                            else:
                                additional_records_bytes += b'\x00' # default hb_rcode (0)
                            if 'edns0' in keys:
                                additional_records_bytes += int.to_bytes(additional_record['edns0'])
                            else:
                                additional_records_bytes += b'\x00' # default edns0 (0)
                            if 'z' in keys:
                                additional_records_bytes += ht(additional_record['z'])
                            else:
                                additional_records_bytes += b'\x00\x00' # default z (0)
                            if 'domain_name' in keys:
                                domain_bytes = Networking.Convert.convert_hostname_to_dns_format(additional_record['domain_name'])
                                if 'data_len' in keys:
                                    additional_records_bytes += ht(additional_record['data_len'])
                                else:
                                    additional_records_bytes += ht(len(domain_bytes))
                                answers_bytes += domain_bytes
                            elif 'data_len' not in keys or additional_record['data_len'] == 0:
                                additional_records_bytes += b'\x00\x00'
                            else:
                                return None
                        # TODO authority records
                        return transaction_id + flags + questions + answer_rrs + authority_rrs + additional_rrs + \
                                queries_bytes + answers_bytes + additional_records_bytes
                        
                    def create_dns_packet(destination_mac, destination_ip, source_udp_port, ip_id, transaction_id, dns_flags, queries, answers, authority_records, additional_records, source_mac='default', source_ip='default', destination_udp_port=53, ttl=64) -> bytes:
                        if source_mac == 'default':
                            source_mac = Networking.Mac.get_mac_address()
                        if source_ip == 'default':
                            source_ip = Networking.IP.get_ip_address()
                        if type(source_mac) != bytes:
                            source_mac = Networking.Convert.convert_mac_address(source_mac)
                        if type(source_ip) != bytes:
                            source_ip = Networking.Convert.convert_ip_address(source_ip)
                        if type(destination_mac) != bytes:
                            destination_mac = Networking.Convert.convert_mac_address(destination_mac)
                        if type(destination_ip) != bytes:
                            destination_ip = Networking.Convert.convert_ip_address(destination_ip)
                        eth_bytes = Networking.Layers.Ethernet.create_ethernet_layer(destination_mac, 0x0800, source_mac=source_mac)
                        if queries is not None:
                            len_queries = len(queries)
                        else: len_queries = 0
                        if answers is not None:
                            len_answers = len(answers)
                        else: len_answers = 0
                        if authority_records is not None:
                            len_authority_records = len(authority_records)
                        else: len_authority_records = 0
                        if additional_records is not None:
                            len_additional_records = len(additional_records)
                        else: len_additional_records = 0
                        dns_bytes = Networking.Layers.IPv4.UDP.DNS.create_dns_layer(
                            transaction_id, dns_flags, len_queries, len_answers, len_authority_records, len_additional_records,
                            queries, answers, authority_records, additional_records)
                        ip_bytes = Networking.Layers.IPv4.create_ipv4_layer(20 + 8 + len(dns_bytes), 
                                    ip_id, 0x11, destination_ip, source_address=source_ip, ttl=ttl)
                        udp_bytes = Networking.Layers.IPv4.UDP.create_udp_layer(source_udp_port, 
                                    destination_udp_port, dns_bytes, source_ip=source_ip, destination_ip=destination_ip)
                        return eth_bytes + ip_bytes + udp_bytes + dns_bytes
                        
    class Sockets:
        def get_receiving_socket():
            s = socket(AF_PACKET, SOCK_RAW, htons(Networking.ETH_P_ALL))
            s.setblocking(False)
            return s
        
        def get_sending_socket(interface='default'):
            if interface == 'default':
                interface = globals.GetDefaultInterface()
            s = socket(AF_PACKET, SOCK_RAW, IPPROTO_RAW)
            s.bind((interface, 0))
            return s
        
        def initialize_sockets():
            globals.sockets.clear()
            globals.sockets['send'] = Networking.Sockets.get_sending_socket()
            globals.sockets['recv'] = Networking.Sockets.get_receiving_socket()
        
        def close_sockets():
            for s in globals.sockets.values():
                s.close()
            globals.sockets.clear()

        def reserve_port():
            s = socket(AF_INET, SOCK_STREAM, 0)
            s.bind(('', 0))
            port = s.getsockname()[1]
            globals.portToSocketMap[port] = s
            return port
        
        def free_reserved_port(port):
            try:
                s = globals.portToSocketMap.pop(port)
                s.close()
            except KeyError:
                pass