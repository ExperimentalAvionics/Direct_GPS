# Direct GPS

This simple Python script reads the NMEA data from GPS receiver connected to Raspberry Pi via USB and sends the data into CAN-Bus network.
Tested with U-BLOX NEO-7M USB GPS receiver

Note: 
This is most simple way to get some basic GPS data at the rate of 1 message per second using default NMEA protocol.
It is very generic and should work with almost all USB GPS units.
Most GPS units can do MUCH more but the code should be a bit more speciffic. Stay tuned for that. :)

At this stage I use the geomag library for magnetic declination lookup. The library was last updated in 2015, so it might be a little bit outdated, but should be reasonably accurate for our purposes.

 
CAN Messages:

CAN ID = 99
Latitude - 4 bytes, Longtitude - 4 bytes

CAN ID = 100
Ground Speed, Altitude, Track True, Track Magnetic - 2 bytes each

See this page for full CAN message map: http://experimentalavionics.com/can-bus/

## Release Notes: ##

### 2023-12-22 ###
The script sends satellite signal information into the CAN bus separately for each of the two constellations GPS (USA) and GLONASS (Russia). 

The messages have arbitration ID 101 and 102 respectively.

The structure of the messages:

The first byte is the number of satellites received by the GPS unit
Other 7 bytes in the CAN message represent satellites signal level from 0 to 14 presented as 4 bit words (one bytes carries information for two satellites)
New version of the Display software uses this information to show the satellites signal levels on the screen.

### 2021-12-14 ###
* Bug fixes in magnetic tracking calculations
* Added satellite signal level CAN messages. Message ID 101 - for GPS and 102 for GLONASS. First byte in the message represents the number of visible satellites. The othe 7 bytes keep the information about signal level in 4 bit words (14 satellites max)

### 2021-06-24 ###
* Ground speed reported to the CAN bus as Knots * 100
