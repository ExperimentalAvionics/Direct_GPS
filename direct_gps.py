#!/usr/bin/python3
#

import can
#import time
import serial

port = "/dev/ttyACM0"

speed=""
alt=""
tracking_true=""
tracking_mag=""
conv_m2ft = 3.28084

print('Bring up CAN0....')

try:
        bus = can.interface.Bus(channel='can0', bustype='socketcan_native')
except OSError:
        print('Cannot find CAN board.')
        exit()

print('CAN is Ready')


print("Receiving GPS data")
ser = serial.Serial(port, baudrate = 9600, timeout = 0.5)
while True:
    data = ser.readline()
#    print("raw:", data) #prints raw data
#    print(data[0:6])

    if data[0:6] == b'$GPRMC':
        sdata = data.decode().split(",")
        if sdata[2] == 'V':
            print("no satellite data available")

#        print("---Parsing GPRMC---")
        time = sdata[1][0:2] + ":" + sdata[1][2:4] + ":" + sdata[1][4:6]
        lat = sdata[3]         #latitude
        dirLat = sdata[4]      #latitude direction N/S
        lon = sdata[5]         #longitute
        dirLon = sdata[6]      #longitude direction E/W
        speed = sdata[7]       #Speed in knots
        trCourse = sdata[8]    #True course
        date = sdata[9][0:2] + "/" + sdata[9][2:4] + "/" + sdata[9][4:6] #date

    if data[0:6] == b'$GPGGA':
        sdata = data.decode().split(",")
        if sdata[2] == 'V':
            print("no satellite data available")

#        print("---Parsing GPGGA---")
        sats = sdata[7]      #number of satelites
        alt = sdata[9]       #GPS altitude
        alt_units = sdata[10] #Altitude units (usually meters)

#        print("Satellites : %s, Altitude : %s(%s)" %  (sats,alt,alt_units))

    if data[0:6] == b'$GPVTG':
        sdata = data.decode().split(",")
        if sdata[2] == 'V':
            print("no satellite data available")

#        print("---Parsing GPVTG---")
        tracking_true = sdata[1]
        tracking_mag = sdata[3]

    if tracking_true == "":
        tracking_true="32768"
    if tracking_mag == "":
        tracking_mag = "32768"
    if speed == "":
        speed = "32768"
    if alt == "":
        alt = "15000"
    GPS_data = bytearray([int(float(speed)) & 0xFF, int(float(speed))>>8, int(float(alt)*conv_m2ft) & 0xFF, int(float(alt)*conv_m2ft)>>8, int(float(tracking_true)) & 0xFF, int(float(tracking_true))>>8, int(float(tracking_mag)) & 0xFF, int(float(tracking_mag))>>8])
    msg = can.Message(arbitration_id=100, data=GPS_data, extended_id=False)

    try:
        bus.send(msg)
#        print("Message sent on {}".format(bus.channel_info))
    except can.CanError:
        print("Message NOT sent")





