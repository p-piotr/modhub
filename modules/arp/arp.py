from screenio import ScreenIO
import curses
import globals
from networking import Networking
from socket import *

running = None

def main(sio : ScreenIO, args : list):
    global running
    running = True
    sr, ss = globals.sockets['recv'], globals.sockets['send']
    packet = Networking.Layers.Ethernet.ARP.create_arp_request_header('255.255.255.255')
    sio.print(''.join(['{:02x} '.format(x) for x in packet]) + '\n')
    sb = ss.send(packet)
    sio.print(f'Sent bytes: {sb}\n')


def finish(sio : ScreenIO):
    global running
    running = False