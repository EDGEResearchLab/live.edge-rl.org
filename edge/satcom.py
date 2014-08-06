# coding: utf-8

import os
import struct
import time


class RockBlock:
    '''Data that all rock blocks will deliver over the iridium network.'''

    '''Unique IMEI of the device'''
    imei = None
    '''The Message Sequence Numer set by RockBLOCK when the message was sent from the
    device to the Iridium Gateway.  The value is an integer in the range 0 to 
    65,535 and is incremented each time a transmit session is successfully completed
    from the device to the Iridium Gateway.  It is a wrap around counter which will
    increment to 0 after reaching 65535.'''
    momsn = None
    '''The date & time (always UTC) that the message was transmitted 12-10-10 10:41:50'''
    transmit_time = None
    '''The approximate latitude of the RockBLOCK at the time it transmitted.'''
    iridium_latitude = None
    '''The approximate longitude of the RockBLOCK at the time it transmitted.'''
    iridium_longitude = None
    '''An Estimate of the accuracy (in km) pf the position information in the previous two fields.'''
    iridium_cep = None
    '''Your message, hex-encoded.'''
    data = None


class EdgeData:
    '''Handler for the hex-encoded data specific to EDGE's reporting over the
    Iridium network.
    '''
    latitude = None # decimal degrees
    longitude = None # decimal degrees
    altitude = None # meters
    speed = None # meters per second
    direction = None # degrees
    utc = None # seconds since epoch
    age = None # milliseconds
    hdr = None # ascii, normalized. Anything outside of the range is ignored.

    def feed_hex(self, hex_data):
        # hexString format: little-endian binary fields
        # data, size bytes, desc.
        struct_string = hex_data.decode('hex')
        data_values = struct.unpack('<%dl' %(len(struct_string) / 4), struct_string)

        '''LAT 4 signed, millionths of degree'''
        self.latitude = self._convert_lat_lon(data_values[0])

        '''LON 4 signed, millionths of degree'''
        self.longitude = self._convert_lat_lon(data_values[1])

        '''ALT 4 signed, centimeters'''
        self.altitude = self._convert_alt(data_values[2])

        '''SPD 2 unsigned, 100ths of knot'''
        self.speed = self._convert_speed(data_values[3] >> 16)

        '''DIR 2 unsigned, 100ths of degree'''
        self.direction = data_values[3] & 0xffff

        '''DAY 4 unsigned, ddmmyy as number'''
        date = str(data_values[4])
        # leading 0's are dropped before transmission.
        if len(date) < 5:
            date = "0" + str(date)

        '''UTC 4 unsigned, hhmmsscc as number'''
        utc = str(data_values[5])
        # leading 0's are dropped before transmission
        if len(utc) < 8:
            utc = "0" + str(utc)
        self.utc = self._convert_time(date + utc)

        '''AGE 4 unsigned, msec since data'''
        self.age = data_values[6]

        # In case there is really messed up data in the HDR field.
        try:
            '''HDR 12 (ascii null-terminated string)'''
            self.hdr = self._normalize_ascii(data[28:-2])
        except Exception as e:
            self.hdr = None

    def _convert_lat_lon(self, data):
        return float(data) / 1000000

    def _convert_alt(self, data):
        return float(data) / 100

    def _convert_speed(self, data):
        return (float(data) / 100) * 0.514444

    def _convert_course(self, data):
        return float(data) / 100

    def _convert_time(self, datetime):
        # expected datetime format: ddmmyyhhmmsscc, cc is dropped.
        in_time = time.strptime(datetime[:-2], "%d%m%y%H%M%S")
        return int(time.mktime(in_time))

    def _normalize_ascii(self, data):
        return "".join(i for i in data if ord(i) < 128)
        
