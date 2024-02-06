#!/usr/bin/python

from http.server import BaseHTTPRequestHandler, HTTPServer
import mimetypes
import asyncio
from datetime import datetime
import websockets
from threading import Thread, Event
from time import time
from queue import Queue, Empty
import functools
import globals
from networking import Networking
from websockets.exceptions import ConnectionClosed, ConnectionClosedError, ConnectionClosedOK

dontPrintCommands = [ 'clear' ] # do not print these commands to the screen
hostName = 'localhost'
httpPort = 8083
wsPort = 8084

class HTTPServerThread:
    class HTTPServerClass(BaseHTTPRequestHandler):
        def getMimeType(self, file):
            mt = mimetypes.guess_type(file)
            if mt:
                return mt[0]
            return None

        def sendFile(self, file):
            try:
                with open('server' + file, 'rb') as f:
                    self.send_response(200)
                    self.send_header('Content-Type', self.getMimeType(file))
                    self.end_headers()
                    self.wfile.write(bytes(f.read()))
            except FileNotFoundError:
                self.send_response(404)

        def do_GET(self):
            if self.path == '/':
                self.sendFile('/index.html')
            else:
                self.sendFile(self.path)

    def run(self, sio):
        webServer = HTTPServer((hostName, httpPort), HTTPServerThread.HTTPServerClass)
        webServer.timeout = 0.5
        print(f'HTTP server is listening at {hostName}:{httpPort}')
        while sio.isRunning(): 
            webServer.handle_request()
        #try:
        #    webServer.serve_forever()
        #except KeyboardInterrupt:
        #    pass
        webServer.server_close()
        print('HTTP Server stopped')

class WebSocketsServerThread:
    def __init__(self, sio):
        self.sio = sio

    async def handler(websocket, path, sio):
        connection_alive = Event()
        connection_alive.set()
        remote_address = websocket.remote_address
        print(f'WS connection from {remote_address[0]}:{remote_address[1]}')
        outputThread = Thread(target=WebSocketsServerThread.threadBetweenCallback, args=(WebSocketsServerThread.outputThread, sio, websocket, connection_alive))
        outputThread.start()
        await WebSocketsServerThread.inputThread(sio, websocket, connection_alive)
        outputThread.join()

    async def server(sio):
        async with websockets.serve(functools.partial(WebSocketsServerThread.handler, sio=sio), 'localhost', wsPort):
            await sio.isRunningAsync()
        print('WebSockets server stopped')

    async def inputThread(sio, websocket, connection_alive):
        while connection_alive.is_set():
            try:
                command = await asyncio.wait_for(websocket.recv(), timeout=0.05)
                #print(f'Data received: {command}')
                if command not in dontPrintCommands:
                    sio.printPrompt()
                    sio.print(command + '\n')
                sio.inputQueue.put(command)
            except TimeoutError:
                pass
            except (ConnectionClosed, ConnectionClosedError, ConnectionClosedOK):
                connection_alive.clear()
                return

    def threadBetweenCallback(func, sio, websocket, connection_alive):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(func(sio, websocket, connection_alive))

    async def outputThread(sio, websocket, connection_alive):
        bufferToSend = ''
        for line in sio.outputBuffer:
            bufferToSend += line
        await websocket.send(bufferToSend)
        while connection_alive.is_set():
            try:
                data = sio.outputQueue.get(timeout=0.02)
                #sio.outputBuffer.append(data)
                await websocket.send(data)
            except Empty:
                pass

    def run(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        print(f'WebSockets server is listening at {hostName}:{wsPort}')
        loop.run_until_complete(WebSocketsServerThread.server(self.sio))
        loop.close()

class ScreenIO:
    def __init__(self):
        self.running = True
        self.currentLineLength = 0
        self.outputBuffer = list()
        self.inputQueue, self.outputQueue = Queue(), Queue()
        self.http = HTTPServerThread()
        self.ws = WebSocketsServerThread(self)
        self.http_t = Thread(target=functools.partial(self.http.run, sio=self))
        self.ws_t = Thread(target=self.ws.run)
        self.http_t.start()
        self.ws_t.start()

    def printPrompt(self):
        self.print('\n' + str(datetime.fromtimestamp(time())), background_color='#A2734C')
        if globals.GetOptionValue('iface') is not None:
            self.print(f' / {Networking.IP.get_ip_address(globals.GetOptionValue("iface"), bytearr=False)}', background_color='#A2734C')
        self.print(' » ')

    def outputStringParser(self, str):
        out_str = ''
        i = 0
        for ch in str:
            if ch == '\t':
                r = self.currentLineLength % 8
                r = 8 - r
                out_str = out_str[:i] + r * '&nbsp'
                self.currentLineLength += r
                i += r * 5
            elif ch == '\n':
                out_str += '<br>'
                self.currentLineLength = 0
                i += 4
            else:
                out_str += ch
                self.currentLineLength += 1
                i += 1
        return out_str

    def styleString(str, font_color='default', background_color='default', bold=False):
        if font_color == 'default' and background_color == 'default' and not bold:
            return str
        out_str = '<span style=\''
        if font_color != 'default':
            out_str += f'color: {font_color};'
        if background_color != 'default':
            out_str += f'background-color: {background_color};'
        if bold:
            out_str += 'font-weight: bold;'
        out_str += f'\'>{str}</span>'
        return out_str

    def print(self, str, font_color='default', background_color='default', bold=False):
        str = self.outputStringParser(str)
        str = ScreenIO.styleString(str, font_color, background_color, bold)
        self.outputQueue.put(str)
        self.outputBuffer.append(str)

    
    def printModulePrompt(self, moduleName):
        self.print('[')
        self.print(str(datetime.now().strftime('%H:%M:%S:%f')))
        self.print('] [')
        self.print(moduleName, font_color='#3DA659')
        self.print('] ') # » 

    def scan(self) -> str:
        return self.inputQueue.get()
    
    def clearScreen(self):
        self.print('\xffclear')
        self.outputBuffer.clear()

    def isRunning(self):
        return self.running
    
    async def isRunningAsync(self):
        while self.isRunning():
            await asyncio.sleep(0.5)
    
    def __del__(self):
        self.running = False