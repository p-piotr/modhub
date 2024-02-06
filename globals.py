import socket

sockets : dict[str, socket.socket]
variables : dict
sockets = {}
variables = {}

ModuleDictionary = {}

AnsiCodes = {
    'HEADER' : '\033[95m',
    'BLUE' : '\033[94m',
    'GREEN' : '\033[92m',
    'RED' : '\033[1m\033[91m',
    'ENDC' : '\033[0m',
    'BOLD' : '\033[1m'
}

CursesColors = {}

def GetOptionValue(option : str):
    try:
        return variables[option]
    except KeyError:
        return None
    
def GetDefaultInterface():
    return GetOptionValue('iface')

def GetReceivingSocket():
    try:
        return sockets['recv']
    except KeyError:
        return None
    
def GetSendingSocket():
    try:
        return sockets['send']
    except KeyError:
        return None