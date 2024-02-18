#!/usr/bin/python

from screenio2 import ScreenIO
from networking import Networking
import globals
from globals import ModuleDictionary, AnsiCodes
import argparse
import os
from threading import Thread
from module_handler import loadModule, runModule
import modules.clear.clear as clear
import modules.set.set as set
import modules.show.show as show
import modules.get.get as get
import modules.arp.spoof as arpspoof
import modules.arp.probe as arpprobe
import modules.test.test as test
import modules.dns.probe as dnsprobe

ModuleDictionary['clear'] = clear
ModuleDictionary['show'] = show
ModuleDictionary['set'] = set
ModuleDictionary['get'] = get
#ModuleDictionary['arp.spoof'] = arpspoof
ModuleDictionary['arp.probe'] = arpprobe
ModuleDictionary['dns.probe'] = dnsprobe
ModuleDictionary['test'] = None

def main(sio : ScreenIO, interface : str):
    if interface is not None:
        set.main(sio, ('set', 'interface', interface))
    while sio.isRunning():
        command = sio.scan()
        commandList = command.split(' ')
        if commandList[0] == 'exit' and len(commandList) == 1:
            sio.print('Sending cleanup signals to all modules...\n')
            cleanup(sio)
            break
        elif commandList[0] == 'load':
            loadModule(sio, commandList[1])
        else:
            runModule(sio, commandList[0], commandList)

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
    check_for_root()
    globals.variables['interfaces'] = Networking.Interfaces.get_network_interfaces()
    parser = argparse.ArgumentParser(description='temporary description')
    parser.add_argument('--interface', help='use specified interface (default: no interface)')
    args = parser.parse_args()
    if args.interface is not None and args.interface not in globals.GetOptionValue('interfaces'):
        print(f'{AnsiCodes["RED"]}{AnsiCodes["BOLD"]}Runtime error{AnsiCodes["ENDC"]}: specified interface \'{args.interface}\' does not exist. Consider using \'show interfaces\' first.')
        exit(-1)
    try:
        sio = ScreenIO()
        main(sio, args.interface)
    except KeyboardInterrupt:
        cleanup(sio)