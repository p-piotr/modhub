from screenio import ScreenIO
import globals

def main(sio : ScreenIO, args : list):
    option = args[1]
    if len(args) > 2:
        sio.print('Error: only one option is allowed at the time.\n')
    else:
        sio.print(f'{globals.GetOptionValue(option)}\n')