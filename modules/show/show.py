from screenio2 import ScreenIO
from networking import Networking
import curses
import globals
from globals import ModuleDictionary, CursesColors

def showIfaces(sio : ScreenIO):
    sio.print('\n')
    for i, iface in enumerate(globals.GetOptionValue('ifaces'), 1):
        ip = Networking.IP.get_ip_address(iface, bytearr=False)
        sio.print(f'\tInterface #{i}:\t')
        sio.print(iface)
        if ip is None:
            sio.print('\t(no IP address available)')
        else:
            sio.print(f'\t(at {ip})')
        if globals.GetOptionValue('iface') == iface:
            sio.print(' (* currently chosen)', bold=True)
        sio.print('\n')
    sio.print('\n')

def showModules(sio : ScreenIO):
    sio.print('\n')
    for module in ModuleDictionary:
        tabs = (1 - len(module) // 8) + 3
        sio.print(f'\t{module}' + tabs * '\t')
        if ModuleDictionary[module] is not None:
            sio.print('loaded\n', font_color='green')
        else:
            sio.print('not loaded\n', font_color='red')
    sio.print('\n')

def main(sio : ScreenIO, args : list):
    value = args[1]
    if value in { 'ifaces', 'interfaces' }:
        showIfaces(sio)
    elif value == 'modules':
        showModules(sio)