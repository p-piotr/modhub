import curses
from threading import Thread, Lock
from queue import Queue, Empty
from time import sleep, time
from datetime import datetime
import globals
from globals import CursesColors
from networking import Networking

dontPrintCommands = [ 'clear', 'exit', 'quit' ] # do not print these commands to the screen

class ScreenIO():
    def __init__(self):
        self._inputQueue = Queue()
        self._buffer = list()
        self._commandQueue = Queue()
        self._printLock =  Lock()
        self._scr = curses.initscr()
        self._inputWindowHeight = 1
        self._height, self._width = self._scr.getmaxyx()
        self._padHeight = 32767
        self._scr.keypad(True)
        self._scr.nodelay(True)
        curses.noecho()
        curses.start_color()
        curses.use_default_colors()
        self.__init_color_pairs()
        self._scr.refresh()
        self._pad = curses.newpad(self._padHeight, self._width)
        self._pad.scrollok(True)
        self._padPos = 0
        self._padRefresh = lambda: self._pad.refresh(self._padPos, 0, 0, 0, self._height - (self._inputWindowHeight + 1), self._width)
        self._inputWindow = self._scr.subwin(self._height - self._inputWindowHeight, 0)
        self._padRefresh()
        self._cursorY, self._cursorX = None, None
        self._running = True
        _scrollThread = Thread(target=self.__scrollThreadFunc)
        _inputThread = Thread(target=self.__inputThreadFunc)
        _scrollThread.start()
        _inputThread.start()

    def isRunning(self):
        return self._running

    def refreshScreen(self):
        self._padRefresh()
        self.__refreshInputWindow()

    def clearScreen(self):
        self._pad.clear()
        self.refreshScreen()

    def print(self, *values):
        self._printLock.acquire()
        self._pad.addstr(*values)
        self._cursorY, self._cursorX = self._pad.getyx()
        if self._cursorY > self._height - (self._inputWindowHeight + 1):
            self._padPos = self._cursorY - self._height + self._inputWindowHeight
        self.refreshScreen()
        self._printLock.release()

    def printPrompt(self):
        self.print(str(datetime.fromtimestamp(time())), CursesColors['WY'])
        if globals.GetOptionValue('iface') is not None:
            self.print(f' / {Networking.IP.get_ip_address(globals.GetOptionValue("iface"), bytearr=False)}', CursesColors['WY'])
        self.print(' » ')

    def scan(self) -> str:
        return self._commandQueue.get()
    
    def __init_color_pairs(self):
        curses.init_pair(1, curses.COLOR_GREEN, -1)
        curses.init_pair(2, curses.COLOR_RED, -1)
        curses.init_pair(3, curses.COLOR_WHITE, curses.COLOR_YELLOW)
        CursesColors['GD'] = curses.color_pair(1)
        CursesColors['RD'] = curses.color_pair(2)
        CursesColors['WY'] = curses.color_pair(3)

    
    def __scrollThreadFunc(self):
        while self.isRunning():
            try:
                ch = self._inputQueue.get(timeout=0.01)
                if ch == curses.KEY_DOWN and self._padPos < self._cursorY - self._height + self._inputWindowHeight:
                    self._padPos += 1
                    self.refreshScreen()
                elif ch == curses.KEY_UP and self._padPos > 0:
                    self._padPos -= 1
                    self.refreshScreen()
                elif ch == curses.KEY_RESIZE:
                    self._height, self._width = self._scr.getmaxyx()
                    self._padPos = self._pad.getyx()[0] - self._height - 1
                    self.refreshScreen()
            except Empty:
                pass

    def __refreshInputWindow(self):
        self._inputWindow.clear()
        self._inputWindow.addstr('» ')
        for ch in self._buffer:
            self._inputWindow.addch(chr(ch))
        self._inputWindow.refresh()

    def __inputThreadFunc(self):
        self.__refreshInputWindow()
        while self.isRunning():
            ch = self._scr.getch()
            if ch == -1:
                sleep(0.01)
            elif ch in [ curses.KEY_DOWN, curses.KEY_UP, curses.KEY_RESIZE ]:
                self._inputQueue.put(ch)
            elif ch == curses.KEY_BACKSPACE:
                if len(self._buffer) > 0:
                    self._buffer.pop()
                    self.__refreshInputWindow()
            elif ch == 10: # ENTER
                command = ''
                for b in self._buffer:
                    command += chr(b)
                self._buffer.clear()
                if command not in dontPrintCommands:
                    self.printPrompt()
                    self.print(command + '\n')
                self._commandQueue.put(command)
            else:
                self._buffer.append(ch)
                self.__refreshInputWindow()

    def __del__(self):
        self._running = False
        self.clearScreen()
        curses.endwin()
        curses.echo()