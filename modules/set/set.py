from screenio2 import ScreenIO
from networking import Networking
import curses
import globals

def printInterfaceDoesntExist(sio : ScreenIO, interface : str):
    globals.PrintErrorPrompt(sio, 'set', None)
    sio.print('interface \'')
    sio.print(ScreenIO.styleString(interface, bold=True))
    sio.print('\' does not exist; check available interfaces using \'')
    sio.print(ScreenIO.styleString('show interfaces', bold=True))
    sio.print('\'.\n')

def main(sio : ScreenIO, args : list):
    try:
        option = args[1]
    except IndexError:
        globals.PrintErrorPrompt(sio, 'set', 'missing arguments\n')
        return
    value = ''.join(args[i] + ' ' for i in range(2, len(args)))
    value = value.rstrip()
    if option == 'interface':
        if value == '':
            sio.print('Usage: set interface [interface]\n')
            return
        if value not in globals.variables['interfaces']:
            printInterfaceDoesntExist(sio, value)
        else:
            Networking.Sockets.close_sockets()
            ip = Networking.IP.get_ip_address(value)
            if ip is None:
                globals.PrintErrorPrompt(sio, 'set', None)
                sio.print('cannot set interface ')
                sio.print(f'{value}', bold=True)
                sio.print(', no IP address available.\n')
            else:
                globals.variables['interface'] = value
                globals.variables['ip_addr'] = Networking.IP.get_ip_address(return_bytes=False)
                globals.variables['br_addr'] = Networking.IP.get_br_address(return_bytes=False)
                globals.variables['hw_addr'] = Networking.Mac.get_mac_address(return_bytes=False)
                globals.variables['gateway'] = Networking.IP.get_gateway_ip_address(return_bytes=False)
                globals.variables['netmask'] = Networking.IP.get_network_mask(return_bytes=False)
                Networking.Sockets.initialize_sockets()
    else:
        globals.variables[option] = value

def finish(sio : ScreenIO):
    pass