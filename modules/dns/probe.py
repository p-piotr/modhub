from networking import Networking
import globals
from screenio2 import ScreenIO
from socket import *
from threading import Thread, Event
from select import select

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
        sio.print('dns.probe: already running.\n')
        return
    running = True
    stop.clear()
    ss = Networking.Sockets.get_sending_socket()
    sr = Networking.Sockets.get_receiving_socket()
    pass

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

def finish(sio : ScreenIO):
    cleanup()