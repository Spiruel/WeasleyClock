import socket
import datetime
import SocketServer
import threading
import ast
import random
import RPi.GPIO as GPIO
from time import sleep, time, gmtime, strftime
import sys
import json
from math import radians, cos, sin, asin, sqrt
import os

from config import locations, clock_positions, accepted_macs

class GPSRequestHandler(SocketServer.BaseRequestHandler):
	def __init__(self, request, client_address, server):
		SocketServer.BaseRequestHandler.__init__(self, request, client_address, server)
		
	def printLog(self, message):
		print("[" + self.client_address[0] + ":" + str(self.client_address[1]) + "] " + message) 
		return message

	def handle(self):
		while True:
			gpsdata = self.request.recv(1024).rstrip('\n')
			if gpsdata == '':
				break
			if gpsdata[-8:] != '__tc15__':
				print 'Invalid data. Not recording data.'
				break
			try:
				gpsdata = gpsdata.split(':')
				mac = ':'.join(gpsdata[3:-1])
				DATA[mac]['latitude'], DATA[mac]['longitude'], DATA[mac]['accuracy'] = [float(i) for i in gpsdata[:3]]
				DATA[mac]['time'] = time()
			except Exception as e:
				self.printLog("Exception caught: closing connection. Message: " + e.message)
				self.request.close()
				break

class ThreadedTCPServer(SocketServer.ThreadingMixIn, SocketServer.TCPServer):
    allow_reuse_address = True
    
    def __init__(self, server_address, RequestHandlerClass):
        SocketServer.TCPServer.__init__(self, server_address, RequestHandlerClass)

def my_tcp_server():
	t = ThreadedTCPServer(('',80), GPSRequestHandler)
	t.serve_forever()
	
class Motor(object):
    def __init__(self, pins, mode=3):
        """Initialise the motor object.
        pins -- a list of 4 integers referring to the GPIO pins that the IN1, IN2
                IN3 and IN4 pins of the ULN2003 board are wired to
        mode -- the stepping mode to use:
                1: wave drive (not yet implemented)
                2: full step drive
                3: half step drive (default)
        """
        self.P1 = pins[0]
        self.P2 = pins[1]
        self.P3 = pins[2]
        self.P4 = pins[3]
        self.mode = mode
        self.deg_per_step = 5.625 / 64  # for half-step drive (mode 3)
        self.steps_per_rev = int(360 / self.deg_per_step)  # 4096
        self.step_angle = 0  # Assume the way it is pointing is zero degrees
        for p in pins:
            GPIO.setup(p, GPIO.OUT)
            GPIO.output(p, 0)

    def _set_rpm(self, rpm):
        """Set the turn speed in RPM."""
        self._rpm = rpm
        # T is the amount of time to stop between signals
        self._T = (60.0 / rpm) / self.steps_per_rev

    # This means you can set "rpm" as if it is an attribute and
    # behind the scenes it sets the _T attribute
    rpm = property(lambda self: self._rpm, _set_rpm)

    def move(self, angle):
	#8375
	steps = int(float(angle / 360.) * 700.)
	if steps > 0:
		print "moving " + `steps` + " steps"	
		self._move_cw_2(steps)
	else:
		print "moving " + `steps` + " steps"
		self._move_acw_2(-steps)

	self.step_angle += angle

    def move_to(self, angle):
        """Take the shortest route to a particular angle (degrees)."""
        # Make sure there is a 1:1 mapping between angle and stepper angle
        target_step_angle = 8 * (int(angle / self.deg_per_step) / 8)
        steps = target_step_angle - self.step_angle
        steps = (steps % self.steps_per_rev)
        if steps > self.steps_per_rev / 2:
            steps -= self.steps_per_rev
            print "moving " + `steps` + " steps"
            if self.mode == 2:
                self._move_acw_2(-steps / 8)
            else:
                self._move_acw_3(-steps / 8)
        else:
            print "moving " + `steps` + " steps"
            if self.mode == 2:
                self._move_cw_2(steps / 8)
            else:
                self._move_cw_3(steps / 8)
        self.step_angle = target_step_angle

    def __clear(self):
        GPIO.output(self.P1, 0)
        GPIO.output(self.P2, 0)
        GPIO.output(self.P3, 0)
        GPIO.output(self.P4, 0)

    def _move_acw_2(self, big_steps):
        self.__clear()
        for i in range(big_steps):
            GPIO.output(self.P3, 0)
            GPIO.output(self.P1, 1)
            sleep(self._T * 2)
            GPIO.output(self.P2, 0)
            GPIO.output(self.P4, 1)
            sleep(self._T * 2)
            GPIO.output(self.P1, 0)
            GPIO.output(self.P3, 1)
            sleep(self._T * 2)
            GPIO.output(self.P4, 0)
            GPIO.output(self.P2, 1)
            sleep(self._T * 2)

    def _move_cw_2(self, big_steps):
        self.__clear()
        for i in range(big_steps):
	    GPIO.output(self.P4, 0)
            GPIO.output(self.P2, 1)
            sleep(self._T * 2)
            GPIO.output(self.P1, 0)
            GPIO.output(self.P3, 1)
            sleep(self._T * 2)
            GPIO.output(self.P2, 0)
            GPIO.output(self.P4, 1)
            sleep(self._T * 2)
            GPIO.output(self.P3, 0)
            GPIO.output(self.P1, 1)
            sleep(self._T * 2)

    def _move_acw_3(self, big_steps):
        self.__clear()
        for i in range(big_steps):
            GPIO.output(self.P1, 0)
            sleep(self._T)
            GPIO.output(self.P3, 1)
            sleep(self._T)
            GPIO.output(self.P4, 0)
            sleep(self._T)
            GPIO.output(self.P2, 1)
            sleep(self._T)
            GPIO.output(self.P3, 0)
            sleep(self._T)
            GPIO.output(self.P1, 1)
            sleep(self._T)
            GPIO.output(self.P2, 0)
            sleep(self._T)
            GPIO.output(self.P4, 1)
            sleep(self._T)

    def _move_cw_3(self, big_steps):
        self.__clear()
        for i in range(big_steps):
            GPIO.output(self.P3, 0)
            sleep(self._T)
            GPIO.output(self.P1, 1)
            sleep(self._T)
            GPIO.output(self.P4, 0)
            sleep(self._T)
            GPIO.output(self.P2, 1)
            sleep(self._T)
            GPIO.output(self.P1, 0)
            sleep(self._T)
            GPIO.output(self.P3, 1)
            sleep(self._T)
            GPIO.output(self.P2, 0)
            sleep(self._T)
            GPIO.output(self.P4, 1)
            sleep(self._T)

def calc_turn(loc1, loc2):
	dist1 = clock[0] - clock[loc1]
	dist2 = clock[0] - clock[loc2]
	if dist1 < 0: dist1 *=-1
	if dist2 < 0: dist2 *=-1
	#print('(%d, %d)' % (dist1,dist2))
	return dist1*gear_ratio + dist2
	
def get_clock_position(data):
	if data:
		lat, long, data_time, accuracy = data['latitude'], data['longitude'], data['time'], data['accuracy']
		location = get_location(lat,long,data_time,last_time,last_location,accuracy) #gets location according to gps data that has been read in
	else:
		return 4

	if location == 'None':
		return 4
	else:
		return clock_positions[location]
	
def haversine(lon1, lat1, lon2, lat2):
    """
    Calculate the great circle distance between two points 
    on the earth (specified in decimal degrees)
    """
    # convert decimal degrees to radians 
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])

    # haversine formula 
    dlon = lon2 - lon1 
    dlat = lat2 - lat1 
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a)) 
    r = 6371E3 # Radius of earth in kilometers. Use 3956 for miles
    return c * r
	
def get_location(x,y,data_time,last_time,last_location,accuracy,inactivity_time=60*10):
    if data_time == last_time:
        if time() - last_time > inactivity_time and last_location != 'LowesBarnBank': #if no new gps data has arrived in a period of time
            print 'Data has not updated for a while. Mortal Peril!'
            return 'MortalPeril'
	if time() - last_time > 0.1*inactivity_time:
	    print 'Data not updated, but not yet in Mortal Peril.'

    last_time = data_time #this is to check data is updating. If it is not then Mortal Peril takes place
    
    if accuracy > 100:
        print 'Warning: Inaccurate GPS data. Accuracy:', accuracy
        return 'None'

    for i in locations:
        target_x, target_y, R = locations[i][0][0], locations[i][0][1], locations[i][1]
        if haversine(target_x, target_y, x, y) <= R: #goes through locations with given radii and checks to see if given point lies within radius
            print 'Location:', i
            return i
         
    durhamperipheryCheck = haversine(54.772883, -1.576377, x, y)
    if durhamperipheryCheck >= 2000 and durhamperipheryCheck == 7500: #checks to see if location lies in a band outside the city
        print 'Location: Durham Periphery'
        return 'DurhamPeriphery'
        
    else:
        if last_location != [0,0] and last_location != 'LowesBarnBank' and last_location != 'MortalPeril' and last_location != 'None' and haversine(last_location[0], last_location[1], x, y) > 10 and haversine(last_location[0], last_location[1], x, y) < 15:  #if in no given location, but moving, returns travelling state
            print 'Travelling? Speed:', haversine(last_location[0], last_location[1]/(time()-last_time), x, y)
            return 'None' #Travelling
        elif last_location != 'LowesBarnBank':
            print 'Not found in any location. Mortal Peril!'
            return 'MortalPeril'
	else:
	    return 'None'
		
if __name__ == '__main__':
	DATA = {i: {} for i in accepted_macs}
	 
	threading.Thread(target=my_tcp_server).start()
	
	gear_ratio = 12
	clock = dict()
	N = 8
	for i in range(N):
		sep = 360/N
		clock[i] = i*sep # 0 == midnite/noon
		
	GPIO.setmode(GPIO.BOARD)
	m = Motor([11,12,13,15])
	m.rpm = 15
	print "Pause in seconds: " + `m._T`
	
	clock_position, last_time, last_location = 0, 0, [0,0]
	oldpos1, oldpos2 = 0, 0
	sleep(5)
	while True:
		try:
			if any(DATA[i] for i in DATA.keys()):		
				if accepted_macs[0] in DATA.keys():
					loc1 = get_clock_position(DATA[accepted_macs[0]])
				else:
					loc1 = clock_positions['MortalPeril']
				if accepted_macs[1] in DATA.keys():
					loc2 = get_clock_position(DATA[accepted_macs[1]])
				else:
					loc2 = clock_positions['MortalPeril']
					
				#loc1 = random.randint(0,N-1)
				#loc2 = random.randint(0,N-1)
				angle_turn = calc_turn(loc1,loc2)-calc_turn(oldpos1,oldpos2)
				if angle_turn > 180*gear_ratio:
					angle_turn = 180*gear_ratio - angle_turn
				#print str(loc1) + ':' + str(loc2) + ' from ' + str(oldpos1) + ':' + str(oldpos2)
				
				if angle_turn != 0:
					print 'angle_turn', angle_turn
					m.move(angle_turn)
					sleep(5)

					oldpos1, oldpos2 = loc1, loc2

				# clock_position, angle_to_move, last_time, last_location = update_time(clock_position, last_time, last_location)
				# print 'Checked clock!'
				sleep(5)
		except KeyboardInterrupt:
			print 'Moving to default position.'
			angle_turn = calc_turn(0,0)-calc_turn(oldpos1,oldpos2)
			if angle_turn > 180*gear_ratio:
				angle_turn = 180*gear_ratio - angle_turn
			print 'angle_turn', angle_turn
			m.move(angle_turn)
			sleep(1)
			GPIO.cleanup()
			sleep(2)
			print 'EXITING!'
			sys.exit()
