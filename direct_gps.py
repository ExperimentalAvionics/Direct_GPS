#!/usr/bin/python3
#
#------------------ Functions --------------------------------------
# Function to convert NMEA coordinates into signed decimal degrees
def NMEA2DEC(nmea_value , nmea_sign ):
    Degrees = int(float(nmea_value)/100)
    Minutes = float(nmea_value) - Degrees * 100
    DecimalDegrees = Degrees + Minutes/60
    if nmea_sign == "S" or nmea_sign == "W":
        DecimalDegrees = DecimalDegrees * (-1)

    return DecimalDegrees;

#-----------------End Of Functions --------------------------------


import can
#import time
import serial
import geomag	#magnetic declination lookup library

port = "/dev/ttyACM0"

speed=""
alt=""
tracking_true=""
tracking_mag=""
conv_m2ft = 3.28084
Msg_Ready = False
lat = 0
lon = 0


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
        lat = NMEA2DEC(sdata[3], sdata[4]) * 1000000
        lon = NMEA2DEC(sdata[5], sdata[6]) * 1000000
        speed = sdata[7]       #Speed in knots
        trCourse = sdata[8]    #True course
        date = sdata[9][0:2] + "/" + sdata[9][2:4] + "/" + sdata[9][4:6] #date

        GPS_data = bytearray([int(lat) & 0xFF, int(lat)>>8 & 0xFF, int(lat)>>16 & 0xFF, int(lat)>>24 & 0xFF, int(lon) & 0xFF,  int(lon)>>8 & 0xFF, int(lon)>>16 & 0xFF, int(lon)>>24 & 0xFF])
        msg = can.Message(arbitration_id=99, data=GPS_data, extended_id=False)
        Msg_Ready = True
 #       print("Lat : %s, Lon : %s, Speed: %s, trCourse: %s" %  (lat, lon, speed, trCourse))

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
#        tracking_mag = sdata[3]	#Theoretically the GPS might have a lookup table for magnetic declination. If it does this line might work

# if there is no data (for example the gps is not moving) return a crazy large number to indicate that
        if tracking_true == "":
            tracking_true = "32768"
            tracking_mag  = "32768"

# Since our GPS receiver does not have the lookup table for declination, we use the geomag library
        if int(tracking_true) >=0 and int(tracking_true)<=360:
            tracking_mag = tracking_true + geomag.declination(lat/1000000, lon/1000000)

        speed = sdata[5]

        if speed == "":
            speed = "32768"
        if alt == "":
            alt = "15000"

        GPS_data = bytearray([int(float(speed)) & 0xFF, int(float(speed))>>8, int(float(alt)*conv_m2ft) & 0xFF, int(float(alt)*conv_m2ft)>>8, int(float(tracking_true)) & 0xFF, int(float(tracking_true))>>8, int(float(tracking_mag)) & 0xFF, int(float(tracking_mag))>>8])
        msg = can.Message(arbitration_id=100, data=GPS_data, extended_id=False)
        Msg_Ready = True
#        print("Speed: %s, Alt : %s, tracking_true: %s, tracking_mag: %s" %  (speed, alt, tracking_true, tracking_mag))
    if  Msg_Ready:
        try:
            bus.send(msg)
#            print("Message sent on {}".format(bus.channel_info))
        except can.CanError:
            print("Message NOT sent")
    Msg_Ready = False



