from screenio import ScreenIO
from networking import Networking
import curses
import globals
from globals import ModuleDictionary, CursesColors

def showIfaces(sio : ScreenIO):
    sio.print('\n')
    for i, iface in enumerate(globals.GetOptionValue('ifaces'), 1):
        ip = Networking.IP.get_ip_address(iface)
        sio.print(f'\tInterface #{i}:\t')
        sio.print(iface, curses.A_BOLD)
        if ip == 'null':
            sio.print('\t(no IP address available)')
        else:
            sio.print(f'\t(at {ip})')
        if globals.GetOptionValue('iface') == iface:
            sio.print(' (* currently chosen)', CursesColors['GD'] | curses.A_BOLD)
        sio.print('\n')
    sio.print('\n')

def showModules(sio : ScreenIO):
    sio.print('\n')
    for module in ModuleDictionary:
        sio.print(f'\t{module}\t')
        if ModuleDictionary[module] is not None:
            sio.print('imported\n', CursesColors['GD'])
        else:
            sio.print('not imported\n', CursesColors['RD'])
    sio.print('\n')

def main(sio : ScreenIO, args : list):
    value = args[1]
    if value == 'ifaces':
        showIfaces(sio)
    elif value == 'modules':
        showModules(sio)