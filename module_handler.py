from screenio2 import ScreenIO
from importlib import import_module
from globals import ModuleDictionary
from threading import Thread
import sys

def loadModule(sio : ScreenIO, moduleName : str):
    if '.' in moduleName:
        fullModulePath = 'modules.' + moduleName
    else:
        fullModulePath = 'modules.' + moduleName + '.' + moduleName

    try:
        module = import_module(fullModulePath)
    except ModuleNotFoundError:
        printModuleNotFound(sio, moduleName)
        return

    if not isStandaloneModule(module):
        printModuleIsNotStandalone(sio, moduleName)
        del sys.modules[fullModulePath]
        return
    ModuleDictionary[moduleName] = module

def isStandaloneModule(module):
    return hasattr(module, 'main') and hasattr(module, 'finish')
        
def printModuleNotFound(sio : ScreenIO, moduleName : str):
    sio.print('Error: module \'')
    sio.print(f'{format(moduleName)}', bold=True)
    sio.print('\' cannot be found.\n')

def printModuleNotLoaded(sio : ScreenIO, moduleName : str):
    sio.print('Module \'')
    sio.print(moduleName, bold=True)
    sio.print('\' is not loaded. Use \'')
    sio.print(f'load {format(moduleName)}', bold=True)
    sio.print('\' first.\n')

def printModuleIsNotStandalone(sio : ScreenIO, moduleName : str):
    sio.print('Module \'')
    sio.print(moduleName, bold=True)
    sio.print('\' is not a standalone module, so it cannot be loaded on its own.\n')

def runModule(sio : ScreenIO, moduleName : str, args : list):
    if moduleName in ModuleDictionary:
        if ModuleDictionary[moduleName] is None: # not imported
            printModuleNotLoaded(sio, moduleName)
        else:
            th = Thread(target=ModuleDictionary[moduleName].main, args=(sio, args))
            th.start()
    else:
        printModuleNotFound(sio, moduleName)