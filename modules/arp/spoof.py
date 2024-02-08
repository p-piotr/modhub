from screenio2 import ScreenIO
import globals
from networking import Networking
from socket import *
from threading import Thread, Event

stop = Event()
ss, sr = None, None
running = False
threads = []

def main(sio : ScreenIO, args : list):
    global stop, ss, sr, running, threads
    if len(args) > 1 and args[1] == 'stop':
        cleanup()
        return
    if running:
        sio.print('arp.spoof: already running.\n')
        return
    running = True

def cleanup():
    global stop, ss, sr, running, threads
    stop.set()
    running = False
    for thread in threads:
        thread.join()
    if ss is not None:
        ss.close()
        ss = None
    if sr is not None:
        sr.close()
        sr = None
    return

def finish(sio : ScreenIO):
    cleanup()