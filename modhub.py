#!/usr/bin/python

from screenio2 import ScreenIO
from networking import Networking
import globals
from globals import ModuleDictionary, AnsiCodes
import curses
import argparse
import os
from time import sleep
from threading import Thread
from importlib import import_module
import modules.clear.clear as clear
import modules.set.set as set
import modules.show.show as show
import modules.get.get as get
import modules.arp.arp as arp
import modules.netprobe.netprobe as netprobe

ModuleDictionary['clear'] = clear
ModuleDictionary['show'] = show
ModuleDictionary['set'] = set
ModuleDictionary['get'] = get
ModuleDictionary['arp'] = arp
ModuleDictionary['netprobe'] = netprobe
ModuleDictionary['test'] = None

def importModule(sio : ScreenIO, moduleName : str):
    try:
        module = import_module('modules.' + moduleName + '.' + moduleName)
        ModuleDictionary[moduleName] = module
    except ModuleNotFoundError:
        printModuleNotFound(sio, moduleName)
        
def printModuleNotFound(sio : ScreenIO, moduleName : str):
    sio.print('Error', curses.A_BOLD | globals.CursesColors['RD'])
    sio.print(': module \'')
    sio.print(f'{format(moduleName)}', curses.A_BOLD)
    sio.print('\' cannot be found.\n')

def printModuleNotLoaded(sio : ScreenIO, moduleName : str):
    sio.print('Module \'')
    sio.print(moduleName, curses.A_BOLD)
    sio.print('\' is not loaded. Use \'')
    sio.print(f'load {format(moduleName)}', curses.A_BOLD)
    sio.print('\' first.\n')

def main(sio : ScreenIO, interface : str):
    if interface is not None:
        set.main(sio, ('set', 'iface', interface))
    while sio.isRunning():
        command = sio.scan()
        commandList = command.split(' ')
        if commandList[0] in [ 'exit', 'quit' ] and len(commandList) == 1:
            sio.print('\nFinishing...\n')
            cleanup(sio)
            break
        elif commandList[0] == 'load':
            importModule(sio, commandList[1])
        elif commandList[0] in ModuleDictionary:
            if ModuleDictionary[commandList[0]] is None: # not imported
                printModuleNotLoaded(sio, commandList[0])
                continue
            th = Thread(target=ModuleDictionary[commandList[0]].main, args=(sio, commandList))
            th.start()
        else:
            sio.print(f'Error: command \"{command}\" not found\n')

def cleanup(sio : ScreenIO):
    threads = list()
    for module in ModuleDictionary.values():
        try:
            t = Thread(target=module.finish, args=(sio,))
            t.start()
            threads.append(t)
        except AttributeError:
            pass
    for th in threads:
        th.join()
    Networking.Sockets.close_sockets()
    sio.__del__()

def check_for_root():
    uid = os.getuid()
    if uid != 0:
        print(f'{AnsiCodes["RED"]}{AnsiCodes["BOLD"]}Runtime error{AnsiCodes["ENDC"]}: must be run as root.')
        exit(-1)

if __name__ == '__main__':
    #check_for_root()
    globals.variables['ifaces'] = Networking.Interfaces.get_network_interfaces()
    parser = argparse.ArgumentParser(description='temporary description')
    parser.add_argument('--interface', help='use specified interface (default: no interface)')
    args = parser.parse_args()
    if args.interface is not None and args.interface not in globals.GetOptionValue('ifaces'):
        print(f'{AnsiCodes["RED"]}{AnsiCodes["BOLD"]}Runtime error{AnsiCodes["ENDC"]}: specified interface \'{args.interface}\' does not exist. Consider using \'show ifaces\' first.')
        exit(-1)
    try:
        sio = ScreenIO()
        main(sio, args.interface)
    except KeyboardInterrupt:
        sio.print('\nFinishing...\n')
        cleanup(sio)