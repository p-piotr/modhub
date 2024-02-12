from screenio2 import ScreenIO
import globals
from networking import Networking
from socket import *
from binary_operations import binary_and, binary_not
from threading import Thread, Event
from select import select

stop = Event()
ss, sr = None, None
running = False
threads = []

def main(sio : ScreenIO, args : list):
    global stop, ss, sr, running, threads
    if len(args) > 1 and args[1] == 'stop':
        cleanup()
        return
    if running:
        sio.print('net.probe: already running.\n')
        return
    running = True
    stop.clear()
    globals.variables['host_map'] = {}
    gateway = Networking.IP.get_network_gateway()
    netmask = Networking.IP.get_network_mask()
    potential_hosts = get_potential_hosts(gateway, netmask)
    ss = Networking.Sockets.get_sending_socket()
    sr = Networking.Sockets.get_receiving_socket()
    sr.setblocking(False)
    t_s = Thread(target=send_arp_requests, args=(sio, ss, potential_hosts, stop))
    t_r = Thread(target=listen_for_arp_replys, args=(sio, sr, potential_hosts, globals.variables['host_map'], stop))
    t_s.start()
    t_r.start()
    threads.append(t_s)
    threads.append(t_r)

def get_potential_hosts(gateway, netmask):
    hosts = set()
    br_address = Networking.IP.get_br_address()
    own_address = Networking.IP.get_ip_address()
    i = lambda v : int.from_bytes(v)
    bitmask = binary_not(i(netmask))
    for j in range(bitmask, 0, -1):
        j &= bitmask
        host = int(binary_and(i(gateway), i(netmask)) + j).to_bytes(4, 'big')
        if host != br_address and host != own_address:
            hosts.add(host)
    hosts = sorted(list(hosts))
    return hosts

def process_arp_packet(sio : ScreenIO, data : bytes, potential_hosts : list, host_map : dict):
    arp = Networking.Layers.Ethernet.ARP.interpret_arp_layer(data)
    if arp.opcode == 2 and bytes(arp.sender_ip_address) in potential_hosts: # opcode (2) == reply
        if bytes(arp.sender_ip_address) in host_map.keys():
            if bytes(arp.sender_mac_address) != host_map[bytes(arp.sender_ip_address)]:
                sio.printModulePrompt('net.probe')
                sio.print(f'{Networking.Convert.convert_ip_address(arp.sender_ip_address)} is now available at {Networking.Convert.convert_mac_address(arp.sender_mac_address)}\n')
                host_map[bytes(arp.sender_ip_address)] = bytes(arp.sender_mac_address)
        else:
            sio.printModulePrompt('net.probe')
            sio.print(f'{Networking.Convert.convert_ip_address(arp.sender_ip_address)} found at {Networking.Convert.convert_mac_address(arp.sender_mac_address)}\n')
            host_map[bytes(arp.sender_ip_address)] = bytes(arp.sender_mac_address)

def listen_for_arp_replys(sio : ScreenIO, sr : socket, potential_hosts : list, hosts : dict, stop : Event):
    while not stop.is_set():
        ready = select([sr], [], [], 0.5)
        if ready[0]:
            data = sr.recv(4096)
            eth = Networking.Layers.Ethernet.interpret_ethernet_layer(data)
            if eth.type == 0x0806:
                process_arp_packet(sio, data[14:], potential_hosts, hosts)
    sio.print('net.probe: listening for ARP replys stopped.\n')

def send_arp_requests(sio : ScreenIO, ss : socket, potential_hosts : list, stop : Event):
    while True:
        for potential_host in potential_hosts:
            arp = Networking.Layers.Ethernet.ARP.create_arp_request_packet(destination_ip=potential_host)
            ss.send(arp)
        flag = stop.wait(10)
        if flag:
            break
    sio.print('net.probe: sending ARP packets stopped.\n')

def cleanup():
    global stop, ss, sr, running, threads
    stop.set()
    running = False
    for thread in threads:
        thread.join()
    if ss is not None:
        ss.close()
        ss = None
    if sr is not None:
        sr.close()
        sr = None

def finish(sio : ScreenIO):
    cleanup()