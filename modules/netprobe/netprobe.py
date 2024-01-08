from screenio import ScreenIO
import curses
import globals
from networking import Networking
from socket import *

running = None

def main(sio : ScreenIO, args : list):
    global running
    if not running:
        running = True
        sr, ss = globals.GetReceivingSocket(), globals.GetSendingSocket()
        gateway = Networking.Interfaces.get_network_gateway('wlan0', bytearr=False)
        sio.print(gateway + '\n')
    else:
        sio.print('net.probe: already running\n')