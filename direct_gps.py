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

sn_array = [0] * 14
k = 0


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

    if data[0:6] == b'$GPRMC' or data[0:6] == b'$GNRMC':
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
#        print("GPRMC/$GNRMC = Lat : %s, Lon : %s, Speed: %s" %  (lat, lon, speed))

# Pure GPS message - GPGGA
# Some  GPS units  use conmination of  GPS and GLONAS sat's
# These units transmit GNGGA message by default

    if data[0:6] == b'$GPGGA' or data[0:6] == b'$GNGGA':
        sdata = data.decode().split(",")
        if sdata[2] == 'V':
            print("no satellite data available")

#        print("---Parsing GPGGA---")
        sats = sdata[7]      #number of satelites
        alt = sdata[9]       #GPS altitude
        alt_units = sdata[10] #Altitude units (usually meters)

#        print("Satellites : %s, Altitude : %s(%s)" %  (sats,alt,alt_units))

    if data[0:6] == b'$GPVTG' or data[0:6] == b'$GNVTG':
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
        if int(float(tracking_true)) >=0 and int(float(tracking_true))<=360:
            tracking_mag = int(float(tracking_true)) + geomag.declination(float(lat)/1000000, float(lon)/1000000)

        speed = sdata[5]

        if speed == "":
            speed = "327.68"
        if alt == "":
            alt = "15000"

        speed = float(speed)*100

        GPS_data = bytearray([int(float(speed)) & 0xFF, int(float(speed))>>8, int(float(alt)*conv_m2ft) & 0xFF, int(float(alt)*conv_m2ft)>>8, int(float(tracking_true)) & 0xFF, int(float(tracking_true))>>8, int(float(tracking_mag)) & 0xFF, int(float(tracking_mag))>>8])
        msg = can.Message(arbitration_id=100, data=GPS_data, extended_id=False)
        Msg_Ready = True
 #       print("GPVTG/GNVTG Speed: %s, Alt : %s, tracking_true: %s, tracking_mag: %s" %  (speed, alt, tracking_true, tracking_mag))
 
# this block process the information about visible satellites for GPS and GLONASS constellations
# its purpose is to track strange disappearance (low signal or jamming) of GPS satellites observed recently in the area where we are based.
#
# one GPGSV or GLGSV message has information about 4 satellites
# multiple messages for the same constellation can be sent sequentially 
# this block forms a CAN messafe consisting of 
#       constellation identifier (CAN ID)
#       number of satellites visible for the constellation (first byte)
#       S/N ratio for each visible satellite represented as a 4-bit number (0-14) fitted in the rest of the 7 bytes of the message
#           S/N ratio usually presented as a number from 0 to 99. So the value needs scaled down to 0-14 leaving value 15 to represent NULL (not tracked satellite)
# so maximum of 14 satellites can be reported for each constellation. It is a minor limitation :)
 
    if data[0:6] == b'$GPGSV' or data[0:6] == b'$GLGSV':
    
        if data[0:6] == b'$GPGSV':
            sn_armitration_id = 101  # GPS
        else:
            sn_armitration_id = 102  # GLONASS
    
#        print("raw:", data) #prints raw data
        sdata = data.decode().split(",")
        sn_msg_count = int(sdata[1])
#        print("Msg Count:",sn_msg_count)
        sn_msg_ix = int(sdata[2])
#        print("Msg Ix",sn_msg_ix)
        sn_size = int(sdata[3])
#        print("Sats:",sn_size)
        
        if sn_msg_count > sn_msg_ix:
            top = 4
        else:
            top = sn_size % 4
        
        i = 0
        while i < top:
            sn_tmp = sdata[i*4+7]
            ast_pos = sn_tmp.find('*')
            if sn_tmp.find('*') > -1:
                sn_tmp = sn_tmp[0:ast_pos]

            if k < 14:
                if sn_tmp == '':
                    sn_array[k] = 15
                elif int(sn_tmp) < 10:
                    sn_array[k] = 1
                else:
                    sn_array[k] = int(int(sn_tmp)*14/99)
#                    sn_array[k] = int(sn_tmp)
                    
                k = k+1
                
            i += 1
        
        
        if sn_msg_count == sn_msg_ix:   # is this the last message for the constellation? if so send the CAN message and initialize the variables
            
            SN_Data = bytearray([int(sn_size), int(sn_array[0]) << 4 | int(sn_array[1]), int(sn_array[2]) << 4 | int(sn_array[3]), int(sn_array[4]) << 4 | int(sn_array[5]), int(sn_array[6]) << 4 | int(sn_array[7]), int(sn_array[8]) << 4 | int(sn_array[9]), int(sn_array[10]) << 4 | int(sn_array[11]), int(sn_array[12]) << 4 | int(sn_array[13]),])
            
#            print("sn_array = ", sn_array)
#            print("SN_Data HEX = ", ''.join(format(x, '02x') for x in SN_Data))
            
            msg = can.Message(arbitration_id=sn_armitration_id, data=SN_Data, extended_id=False)
            Msg_Ready = True

            sn_array = [0] * 14
            k = 0
        
#        if len(sn_array) > 14
 
    if  Msg_Ready:
        try:
            bus.send(msg)
#            print("Message sent on {}".format(bus.channel_info))
        except can.CanError:
            print("Message NOT sent")
    Msg_Ready = False
