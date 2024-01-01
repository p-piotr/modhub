from screenio import ScreenIO
from networking import Networking
import curses
import globals
from globals import CursesColors

def printInterfaceDoesntExist(sio : ScreenIO, iface : str):
    sio.print('Interface \'')
    sio.print(iface, curses.A_BOLD)
    sio.print('\' does not exist. Check available interfaces using \'')
    sio.print('show ifaces', curses.A_BOLD)
    sio.print('\'.\n')

def main(sio : ScreenIO, args : list):
    option = args[1]
    value = ''.join(args[i] + ' ' for i in range(2, len(args)))
    value = value.rstrip()
    if option == 'iface':
        if value not in globals.variables['ifaces']:
            printInterfaceDoesntExist(sio, value)
        else:
            for socket in globals.sockets:
                socket.close()
            globals.sockets.clear()
            ip = Networking.IP.get_ip_address(value)
            if ip == 'null':
                sio.print('Error', CursesColors['RD'])
                sio.print(': cannot set this interface, no IP address available.\n')
            else:
                globals.variables['iface'] = value
                globals.variables['ip_addr'] = Networking.IP.get_ip_address(value)
                globals.variables['hw_addr'] = Networking.Mac.get_mac_address(value)
                Networking.Sockets.initialize_sockets()
    else:
        globals.variables[option] = value