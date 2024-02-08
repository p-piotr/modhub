from screenio2 import ScreenIO
from networking import Networking
import globals
from globals import ModuleDictionary

def showInterfaces(sio : ScreenIO):
    sio.print('\n')
    for i, interface in enumerate(globals.GetOptionValue('interfaces'), 1):
        ip = Networking.IP.get_ip_address(interface, return_bytes=False)
        sio.print(f'\tInterface #{i}:\t')
        sio.print(interface)
        if ip is None:
            sio.print('\t(no IP address available)')
        else:
            sio.print(f'\t(at {ip})')
        if globals.GetOptionValue('interface') == interface:
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
    if len(args) < 2:
        sio.print('Error: missing argument(s)\n')
        return
    value = args[1]
    if value == 'interfaces':
        showInterfaces(sio)
    elif value == 'modules':
        showModules(sio)

def finish(sio : ScreenIO):
    pass