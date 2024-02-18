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

portToSocketMap = {}

def PrintErrorPrompt(sio, moduleName, errorMessage):
    sio.print(f'{moduleName}: [')
    sio.print('err', font_color='red')
    sio.print('] ')
    if errorMessage not in [ None, '' ]:
        sio.print(errorMessage)

def GetOptionValue(option, to_str=False):
    try:
        if not to_str:
            return variables[option]
        return str(variables[option])
    except KeyError:
        return None
    
def OptionExists(option):
    k = variables.keys()
    if option in k:
        return True
    return False
    
def GetDefaultInterface():
    return GetOptionValue('interface')

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