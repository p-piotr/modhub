from screenio2 import ScreenIO
import globals
import random
from networking import Networking
from socket import *
from binary_operations import binary_and, binary_not
from threading import Thread, Event
from select import select

stop = Event()
running = False
threads = []

def main(sio : ScreenIO, args : list):
    global running
    if len(args) == 1:
        sio.print('Usage: arp.probe [option]\n')
    else:
        if args[1] == 'help':
            showHelp(sio)
            return
        elif args[1] == 'run':
            if running:
                sio.print('arp.probe: already running.\n')
                return
            run(sio)
            return
        elif args[1] == 'stop':
            cleanup()
            return
        elif args[1] == 'clear_hosts':
            if globals.OptionExists('host_map'):
                globals.variables['host_map'].clear()
            sio.print('arp.probe: hosts cleared.\n')
            return
        elif args[1] == 'show_hosts':
            show_hosts(sio)
            return
        else:
            globals.PrintErrorPrompt(sio, 'arp.probe', None)
            sio.print('unknown option \'')
            sio.print(f'{args[1]}', bold=True)
            sio.print('\'.\n')

def run(sio : ScreenIO):
    global stop, running, threads
    running = True
    stop.clear()
    if not globals.OptionExists('host_map'):
        globals.variables['host_map'] = {}
    gateway = Networking.IP.get_gateway_ip_address()
    netmask = Networking.IP.get_network_mask()
    potential_hosts = get_potential_hosts(gateway, netmask)
    t_s = Thread(target=send_arp_requests, args=(sio, potential_hosts, stop))
    t_r = Thread(target=listen_for_arp_replys, args=(sio, potential_hosts, globals.variables['host_map'], stop))
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

def process_arp_packet(sio : ScreenIO, ss : socket, sr : socket, data : bytes, potential_hosts : list, host_map : dict):
    global perform_dns_lookup
    arp = Networking.Layers.Ethernet.ARP.interpret_arp_layer(data)
    if arp.opcode == 2 and bytes(arp.sender_ip_address) in potential_hosts: # opcode (2) == reply
        if bytes(arp.sender_ip_address) in host_map.keys():
            if bytes(arp.sender_mac_address) != host_map[bytes(arp.sender_ip_address)]['mac']:
                sio.printModulePrompt('arp.probe')
                sio.print(f'{Networking.Convert.convert_ip_address(arp.sender_ip_address)} is now available at {Networking.Convert.convert_mac_address(arp.sender_mac_address)}\n')
                host_map[bytes(arp.sender_ip_address)] = { 'mac' : bytes(arp.sender_mac_address),
                                                          'inactive_for' : 0 }
            else:
                host_map[bytes(arp.sender_ip_address)]['inactive_for'] = 0
        else:
            sio.printModulePrompt('arp.probe')
            sio.print(f'{Networking.Convert.convert_ip_address(arp.sender_ip_address)} found at {Networking.Convert.convert_mac_address(arp.sender_mac_address)}\n')
            host_map[bytes(arp.sender_ip_address)] = { 'mac' : bytes(arp.sender_mac_address),
                                                      'inactive_for' : 0 }

def listen_for_arp_replys(sio : ScreenIO, potential_hosts : list, hosts : dict, stop : Event):
    sr = Networking.Sockets.get_receiving_socket()
    ss = Networking.Sockets.get_sending_socket()
    while not stop.is_set():
        ready = select([sr], [], [], 0.5)
        if ready[0]:
            data = sr.recv(4096)
            eth = Networking.Layers.Ethernet.interpret_ethernet_layer(data)
            if eth.type == 0x0806:
                process_arp_packet(sio, ss, sr, data[14:], potential_hosts, hosts)
    sr.close()
    ss.close()
    sio.print('arp.probe: scanning stopped.\n')

def send_arp_requests(sio : ScreenIO, potential_hosts : list, stop : Event):
    ss = Networking.Sockets.get_sending_socket()
    while True:
        for potential_host in potential_hosts:
            arp = Networking.Layers.Ethernet.ARP.create_arp_request_packet(destination_ip=potential_host)
            ss.send(arp)
        flag = stop.wait(2)
        for key, entry in globals.variables['host_map'].items():
            entry['inactive_for'] += 2
        if flag:
            break
    ss.close()

def show_hosts(sio : ScreenIO):
    i = 1
    if not globals.OptionExists('host_map') or globals.variables['host_map'] == {}:
        globals.PrintErrorPrompt(sio, 'arp.probe', None)
        sio.print('host map not found, run the scan first.\n')
        return
    sio.print('\n')
    host_map = globals.variables['host_map']
    keys = host_map.keys()
    for key in sorted(keys):
        if len(Networking.Convert.convert_ip_address(key)) < 12:
            tabs = 2
        else: tabs = 1
        t = tabs * '\t'
        sio.print(f'\t#{i}:\t\
                IP: {Networking.Convert.convert_ip_address(key)}{t}\
                MAC: {Networking.Convert.convert_mac_address(host_map[key]["mac"])}')
        if running:
            sio.print(f'\tInactive for: {host_map[key]["inactive_for"]}s\n')
        else:
            sio.print('\n')
        i += 1
    sio.print('\n')

def showHelp(sio : ScreenIO):
    sio.print('\nAvailable options:\n\nhelp\t\tshow this message\n'
            'run\t\trun scanning for hosts in chosen network\n'
            'stop\t\tstop scanning\n'
            'show_hosts\tshow already detected hosts\n'
            'clear_hosts\tclear host data\n')

def cleanup():
    global stop, running, threads
    stop.set()
    running = False
    for thread in threads:
        thread.join()

def finish(sio : ScreenIO):
    cleanup()