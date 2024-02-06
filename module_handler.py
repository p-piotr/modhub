from screenio2 import ScreenIO
from importlib import import_module
from globals import ModuleDictionary
from threading import Thread

def importModule(sio : ScreenIO, moduleName : str):
    try:
        module = import_module('modules.' + moduleName + '.' + moduleName)
        ModuleDictionary[moduleName] = module
    except ModuleNotFoundError:
        printModuleNotFound(sio, moduleName)
        
def printModuleNotFound(sio : ScreenIO, moduleName : str):
    sio.print('Error')
    sio.print(': module \'')
    sio.print(f'{format(moduleName)}', bold=True)
    sio.print('\' cannot be found.\n')

def printModuleNotLoaded(sio : ScreenIO, moduleName : str):
    sio.print('Module \'')
    sio.print(moduleName, bold=True)
    sio.print('\' is not loaded. Use \'')
    sio.print(f'load {format(moduleName)}', bold=True)
    sio.print('\' first.\n')

def runModule(sio : ScreenIO, moduleName : str, args : list):
    if moduleName in ModuleDictionary:
        if ModuleDictionary[moduleName] is None: # not imported
            printModuleNotLoaded(sio, moduleName)
        else:
            th = Thread(target=ModuleDictionary[moduleName].main, args=(sio, args))
            th.start()
    else:
        printModuleNotFound(sio, moduleName)