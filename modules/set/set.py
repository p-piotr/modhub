from screenio2 import ScreenIO
from networking import Networking
import curses
import globals
from globals import CursesColors

def printInterfaceDoesntExist(sio : ScreenIO, iface : str):
    sio.print('Interface \'')
    sio.print(ScreenIO.styleString(iface, bold=True))
    sio.print('\' does not exist. Check available interfaces using \'')
    sio.print(ScreenIO.styleString('show ifaces', bold=True))
    sio.print('\'.\n')

def main(sio : ScreenIO, args : list):
    try:
        option = args[1]
    except IndexError:
        sio.print('Error: missing arguments\n')
        return
    value = ''.join(args[i] + ' ' for i in range(2, len(args)))
    value = value.rstrip()
    if option in { 'iface', 'interface' }:
        if value not in globals.variables['ifaces']:
            printInterfaceDoesntExist(sio, value)
        else:
            Networking.Sockets.close_sockets()
            ip = Networking.IP.get_ip_address(value)
            if ip is None:
                sio.print('Error: cannot set this interface, no IP address available.\n')
            else:
                globals.variables['iface'] = value
                globals.variables['ip_addr'] = Networking.IP.get_ip_address(value)
                globals.variables['hw_addr'] = Networking.Mac.get_mac_address(value)
                Networking.Sockets.initialize_sockets()
    else:
        globals.variables[option] = value