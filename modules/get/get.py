from screenio2 import ScreenIO
import globals

def main(sio : ScreenIO, args : list):
    if len(args) == 1:
        sio.print('Usage: get [option]\n')
        return
    option = args[1]
    if len(args) > 2:
        globals.PrintErrorPrompt(sio, 'get', 'only one option is allowed at the time.\n')
    else:
        sio.print(f'{globals.GetOptionValue(option, to_str=True)}\n')

def finish(sio : ScreenIO):
    pass