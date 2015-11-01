import socket
import datetime
import SocketServer
from threading import Thread
import ast
import time

class GPSRequestHandler(SocketServer.BaseRequestHandler):

    def __init__(self, request, client_address, server):
        SocketServer.BaseRequestHandler.__init__(self, request, client_address, server)
        
        return
    def printLog(self, message):
        print("[" + self.client_address[0] + ":" + str(self.client_address[1]) + "] " + message)
        
        return message

    def handle(self):
    
        while True:
            gpsdata = self.request.recv(1024).rstrip('\n')
	    if gpsdata == '':
	        break
	    if gpsdata[-8:] != '__tc15__':
		print 'Invalid data. Not writing to file.'
	        break
            try:
				gpsdata = gpsdata.split(':')
				data = {}
				data['latitude'], data['longitude'], data['accuracy'] = [float(i) for i in gpsdata[:-1]]
				data['time'] = time.time()
				print data
				file = open("file2","w")
				file.write(str(data))
				file.close()
            except Exception as e:
                self.printLog("Exception caught: closing connection. Message: " + e.message)
                self.request.close()
                break

class ThreadedTCPServer(SocketServer.ThreadingMixIn, SocketServer.TCPServer):
    allow_reuse_address = True
    
    def __init__(self, server_address, RequestHandlerClass):
        SocketServer.TCPServer.__init__(self, server_address, RequestHandlerClass)

t = ThreadedTCPServer(('',80), GPSRequestHandler)
t.serve_forever()
