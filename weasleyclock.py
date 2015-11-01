#!/usr/bin/env python

# It works on the Raspberry Pi computer with the standard Debian Wheezy OS and
# the 28BJY-48 stepper motor with ULN2003 control board.

from time import sleep, time
import ast
import json
import RPi.GPIO as GPIO
import sys
from math import radians, cos, sin, asin, sqrt

locations = {
'LowesBarnBank': [(54.766775099999997, -1.5940502000000001),10],
'ScienceSite': [(54.767467, -1.572705),200],
'CityCentre': [(54.776806, -1.575546),150],
'GreyCollege': [(54.764546, -1.575599),100],
'ScarrowHill': [(54.949553, -2.673763),100]
}

clock_positions = {
'GreyCollege': 0,
'ScarrowHill': 1,
'LowesBarnBank': 2,
'Travelling': 3,
'MortalPeril': 4,
'DurhamPeriphery': 5,
'ScienceSite': 6,
'CityCentre': 7
}

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
    r = 6371 # Radius of earth in kilometers. Use 3956 for miles
    return c * r
    
def get_location(x,y,data_time,last_time,last_location,accuracy,inactivity_time=60*10):
    if data_time == last_time:
        if time() - last_time > inactivity_time: #if no new gps data has arrived in a period of time
            print 'Data has not updated for a while. Mortal Peril!'
            return 'MortalPeril'
	if time() - last_time > 0.1*inactivity_time:
	    print 'Data not updated, but not yet in Mortal Peril.'

    if accuracy > 250:
        print 'Warning: Inaccurate GPS data.'

    last_time = data_time
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
        if last_location != [0,0] and haversine(last_location[0], last_location[1], x, y)/(time()-last_time) > 5:  #if in no given location, but moving, returns travelling state
            print 'Travelling? Speed:', haversine(last_location[0], last_location[1], x, y)/(time()-last_time)
            return 'Travelling'
        else:
            print 'Not found in any location. Mortal Peril!'
            return 'MortalPeril'

def get_clock_position(location):
    """Returns the clock position (angle) in which the motor needs to turn to. 
    Motor is at angle 0 each time it turns on as it is only switched on remembering the angle during operation."""
	return clock_positions[location]*(360/len(clock_positions))
   
def update_time(last_clock_position, last_time, last_location):
    reading = True
    while reading == True:
        try:
            file = open('file2', 'r') #open file and read gps data
            readfile = file.read()
            data = ast.literal_eval(str(readfile).replace('\'','\"').replace('u\"','"'))
            reading = False
        except Exception as e:
            print e
    lat, long, data_time, accuracy = data['latitude'], data['longitude'], data['time'], data['accuracy']
    location = get_location(lat,long,data_time,last_time,last_location,accuracy) #gets location according to gps data that has been read in
    clock_position = get_clock_position(location)
    angle_to_move = clock_position
    if clock_position != last_clock_position: #if location is different, switch on motor and make changes
        print 'Location changed, updating clock.'
        sleep(1)
        beep([0.3]*3)
        GPIO.setmode(GPIO.BOARD)
        m =  Motor([11,12,13,15])
        m.rpm = 5
        print 'Moving to angle:', clock_position
        angle_to_move = clock_position - last_clock_position
        m.move_to(angle_to_move)
        GPIO.cleanup()
    return clock_position, angle_to_move, data_time, [lat,long]

def beep(length):
    """Causes a piezo device to beep for a specified duration"""
    if type(length) != list:
        length = [length]
    for i in length:
        GPIO.setmode(GPIO.BOARD)
        GPIO.setup(15, GPIO.OUT)
        start = time()
        while True:
            GPIO.output(15, 1)
            sleep(0.00048828125)
            GPIO.output(15, 0)
            sleep(0.00048828125)
            end = time()
            if end - start >= i:
                GPIO.cleanup()
                sleep(0.15)
                break
                    
if __name__ == "__main__":
    clock_position, last_time, last_location = 0, 0, [0,0]
    GPIO.setmode(GPIO.BOARD)
    m = Motor([11,12,13,15])
    m.rpm = 5
    print "Pause in seconds: " + `m._T`
    m.move_to(90)
    sleep(1)
    m.move_to(0)
    sleep(1)
    m.mode = 2
    m.move_to(90)
    sleep(1)
    m.move_to(0)
    GPIO.cleanup()
    while True:
        try:
            clock_position, angle_to_move, last_time, last_location = update_time(clock_position, last_time, last_location)
            print 'Checked clock!'
            sleep(5)
        except KeyboardInterrupt:
            print 'Moving to default position.'
            GPIO.setmode(GPIO.BOARD)
            m = Motor([11,12,13,15])
            m.rpm = 5
            m.move_to(-clock_position)
            GPIO.cleanup()
            sleep(2)
            sys.exit()
