from networking import Networking
from socket import socket
from select import select
import random
import globals
from screenio2 import ScreenIO
from threading import Thread, Event

stop = Event()
running = False
threads = []

def main(sio : ScreenIO, args : list):
    global stop, running, threads
    if len(args) > 1:
        if args[1] == 'stop':
            cleanup()
            return
    if running:
        sio.print('dns.probe: already running.\n')
        return
    running = True
    stop.clear()
    if not globals.OptionExists('host_map') or globals.variables['host_map'] == {}:
        globals.PrintErrorPrompt(sio, 'dns.probe', None)
        sio.print('cannot get host map to start probing; run ')
        sio.print('arp.probe', bold=True)
        sio.print(' first.\n')
        return
    if not globals.OptionExists('dns_map'):
        globals.variables['dns_map'] = {}
    

def convert_ip_to_reverse_dns_form(ip : str | bytes, return_bytes=True) -> bytes:
    if type(ip) != str:
        ip = Networking.Convert.convert_ip_address(ip)
    l = ip.split('.')
    ret_addr = ''
    for p in reversed(l):
        ret_addr += p + '.'
    ret_addr += 'in-addr.arpa'
    if return_bytes:
        return ret_addr.encode()
    return ret_addr

def convert_ip_from_reverse_dns_form(ip : bytes, return_bytes=True) -> str | bytes:
    ip = ip[:-13]
    return ip
    """
    l = ip.split('.')
    ret_addr = ''
    for p in reversed(l):
        ret_addr += p
        """
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
                
def cleanup():
    global stop, running, threads
    stop.set()
    running = False
    for thread in threads:
        thread.join()

def finish(sio : ScreenIO):
    cleanup()