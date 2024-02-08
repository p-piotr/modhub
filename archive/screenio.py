import curses
import math
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
        self._scr = curses.initscr()
        curses.noecho()
        curses.start_color()
        curses.use_default_colors()
        #curses.curs_set(0) # will be set to visible (1) at the next input window refresh
        self._inputQueue = Queue()
        self._buffer = list()
        self._commandQueue = Queue()
        self._printLock =  Lock()
        self._inputWindowHeight = 1
        self._height, self._width = self._scr.getmaxyx()
        self._padHeight = 32767
        self._scr.keypad(True)
        self._scr.nodelay(True)
        self.__init_color_pairs()
        self._scr.refresh()
        self._pad = curses.newpad(self._padHeight, self._width)
        self._pad.scrollok(True)
        self._padPos = 0
        self._inputWindow = self._scr.subwin(self._height - self._inputWindowHeight, 0)
        self._inputWindow.bkgdset(10)
        self._inputWindowSizeChanged = 0 # 0 - not changed, 1 - increased size (by 1), 2 - decreased size (by 1)
        self._cursorY, self._cursorX = self._height - 1, 2
        self.__padRefresh()
        self._padY, self._padX = 0, 0
        self._running = True
        _scrollThread = Thread(target=self.__scrollThreadFunc)
        _inputThread = Thread(target=self.__inputThreadFunc)
        _scrollThread.start()
        _inputThread.start()

    def isRunning(self):
        return self._running

    def refreshScreen(self):
        self.__padRefresh()
        self.__refreshInputWindow()

    def clearScreen(self):
        self._pad.clear()
        self._padPos = 0
        self.refreshScreen()

    def print(self, *values, refresh=True):
        self._printLock.acquire()
        self._pad.addstr(*values)
        self._padY, self._padX = self._pad.getyx()
        if self._padY > self._height - (self._inputWindowHeight + 1):
            self._padPos = self._padY - self._height + self._inputWindowHeight
        if refresh:
            self.refreshScreen()
        self._printLock.release()

    def printPrompt(self, refresh=True):
        self.print(str(datetime.fromtimestamp(time())), CursesColors['WY'])
        if globals.GetOptionValue('interface') is not None:
            self.print(f' / {Networking.IP.get_ip_address(globals.GetOptionValue("interface"), return_bytes=False)}', CursesColors['WY'], refresh=False)
        self.print(' » ', refresh=refresh)

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
                if ch == curses.KEY_DOWN and self._padPos < self._padY - self._height + self._inputWindowHeight:
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

    def __padRefresh(self):
        self._pad.refresh(self._padPos, 0, 0, 0, self._height - (self._inputWindowHeight + 1), self._width)

    def __refreshInputWindow(self):
        self._inputWindow.clear()
        content_length = len(self._buffer) + 2
        inputWindowHeight = math.ceil((content_length + 1) / self._width)
        self._cursorX = content_length % self._width
        self._cursorY = self._height - 1
        if inputWindowHeight != self._inputWindowHeight:
            if inputWindowHeight - self._inputWindowHeight > 0:
                self._inputWindowSizeChanged = 1
            else:
                self._inputWindowSizeChanged = 2
            self._inputWindowHeight = inputWindowHeight
            #del self._inputWindow
            #self._inputWindow = self._scr.subwin(self._height - self._inputWindowHeight, 0)
            self._inputWindow.resize(self._height - self._inputWindowHeight, 0)
        self._inputWindow.addstr('» ')
        for ch in self._buffer:
            self._inputWindow.addch(ch)
        self._inputWindow.refresh()

    def __inputThreadFunc(self):
        self.refreshScreen()
        while self.isRunning():
            ch = self._scr.getch()
            if ch == -1:
                if self._inputWindowSizeChanged == 1:
                    self.__padRefresh()
                    self._scr.move(self._cursorY, self._cursorX)
                    self._inputQueue.put(curses.KEY_DOWN)
                    self._inputWindowSizeChanged = 0
                elif self._inputWindowSizeChanged == 2:
                    self.__padRefresh()
                    self._scr.move(self._cursorY, self._cursorX)
                    self._inputQueue.put(curses.KEY_UP)
                    self._inputWindowSizeChanged = 0
                sleep(0.01)
            elif ch in [ curses.KEY_DOWN, curses.KEY_UP, curses.KEY_RESIZE ]:
                self._inputQueue.put(ch)
            elif ch == 18: # CTRL + R
                self.refreshScreen()
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
                    self.printPrompt(refresh=False)
                    self.print(command + '\n')
                self._commandQueue.put(command)
                self.__refreshInputWindow()
            else:
                if chr(ch).isprintable():
                    self._buffer.append(ch)
                    self.__refreshInputWindow()

    def __del__(self):
        self._running = False
        self.clearScreen()
        curses.endwin()
        curses.echo()