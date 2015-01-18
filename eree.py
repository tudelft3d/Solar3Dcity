#!/usr/bin/env python
# Copyright (C) 2013 Nathan Charles
#
# This program is free software. See terms in LICENSE file.
"""Global EERE Weather Data Sources"""

import os
import csv
import zipfile
import tempfile
import datetime
try:
    from urllib.request import urlopen
except ImportError:
    from urllib import urlopen

#-- Timezone
import pytz
local_tz = pytz.timezone('Europe/Amsterdam')

WEATHER_DATA_PATH = os.environ['HOME'] + "/weather_data"
SRC_PATH = os.path.dirname(os.path.abspath(__file__))

DATA_EXTENTIONS = {'SWERA':'epw', \
        'CSWD':'epw', \
        'CWEC':'epw', \
        'ETMY':'epw', \
        'IGDG':'epw', \
        'IMGW':'epw', \
        'INETI':'epw', \
        'ISHRAE':'epw', \
        'ITMY':'epw', \
        'IWEC':'epw', \
        'KISR':'epw', \
        'MSI':'epw', \
        'NIWA':'epw', \
        'RMY':'epw', \
        'SWEC':'epw', \
        'TMY':'epw', \
        'TMY2':'epw', \
        'TMY3':'epw', \
        'IWEC':'epw'}

try:
    os.listdir(WEATHER_DATA_PATH)
except OSError:
    try:
        os.mkdir(WEATHER_DATA_PATH)
    except IOError:
        pass

def _muck_w_date(record):
    """muck with the date because EPW starts counting from 1 and goes to 24"""
    d = datetime.datetime(int(record['Year']), int(record['Month']), \
            int(record['Day']), int(record['Hour'])%24, \
            int(record['Minute'])%60)
    h_off = int(record['Hour']) //60 
    if h_off > 0:
        d += datetime.timedelta(hours=h_off )
    d_off = int(record['Hour'])//24
    if d_off > 0:
        d += datetime.timedelta(days=d_off)
    return d

def download(url):
    """download TMY3 file"""
    data_handle = urlopen(url)
    with tempfile.TemporaryFile(suffix='.zip', dir=WEATHER_DATA_PATH) \
            as local_file:
        local_file.write(data_handle.read())
        compressed_file = zipfile.ZipFile(local_file, 'r')
        compressed_file.extractall(WEATHER_DATA_PATH)
        local_file.close()

def _eere_url(station_code):
    """build EERE EPW url for station code"""
    baseurl = 'http://apps1.eere.energy.gov/buildings/energyplus/weatherdata/'
    return baseurl + _station_info(station_code)['url']

def _station_info(station_code):
    """filename based meta data for a station code"""
    url_file = open(SRC_PATH + '/eree.csv')
    for line in csv.DictReader(url_file):
        if line['station_code'] == station_code:
            return  line
    raise KeyError('Station not found')


def _basename(station_code):
    "region, country, weather_station, station_code, data_format, url"
    info = _station_info(station_code)
    basename = '%s_%s.%s_%s.%s' % (info['country'], \
            info['weather_station'],\
            info['station_code'], info['data_format'], \
            DATA_EXTENTIONS[info['data_format']])
    return basename

class EPWdata(object):
    """EPW weather generator"""
    def __init__(self, station_code):
        #filename = path + usaf + 'TY.csv'
        filename = WEATHER_DATA_PATH + '/' + _basename(station_code)
        self.csvfile = None
        try:
            self.csvfile = open(filename)
        except IOError:
            print("File not found")
            print("Downloading ...")
            download(_eere_url(station_code))
            self.csvfile = open(filename)
        fieldnames = ["Year", "Month", "Day", "Hour", "Minute", "DS", \
                "Drybulb (C)", "Dewpoint (C)", "Relative Humidity", \
                "Pressure (Pa)", "ETR (W/m^2)", "ETRN (W/m^2)", "HIR (W/m^2)", \
                "GHI (W/m^2)", "DNI (W/m^2)", "DHI (W/m^2)", "GHIL (lux)", \
                "DNIL (lux)", "DFIL (lux)", "Zlum (Cd/m2)", "Wdir (degrees)", \
                "Wspd (m/s)", "Ts cover", "O sky cover", "CeilHgt (m)", \
                "Present Weather", "Pw codes", "Pwat (cm)", "AOD (unitless)", \
                "Snow Depth (cm)", "Days since snowfall"]
        station_meta = self.csvfile.readline().split(',')
        self.station_name = station_meta[1]
        self.CC = station_meta[3]
        self.station_fmt = station_meta[4]
        self.station_code = station_meta[5]
        self.lat = station_meta[6]
        self.lon = station_meta[7]
        self.TZ = float(station_meta[8])
        self.ELEV = station_meta[9]
        dummy = ""
        for _ in range(7):
            dummy += self.csvfile.readline()
        self.epw_data = csv.DictReader(self.csvfile, fieldnames=fieldnames)

    def __iter__(self):
        return self

    def next(self):
        """generator handle"""
        record = self.epw_data.next()
        local_time = _muck_w_date(record)
        record['datetime'] = local_time
        # record['utc_datetime'] = local_time - datetime.timedelta(hours=self.TZ)
        localdt = local_tz.localize(record['datetime'])
        record['utc_datetime'] = localdt.astimezone(pytz.UTC)
        return record
        'LOCATION,BEEK,-,NLD,IWEC Data,063800,50.92,5.78,1.0,116.0'

    def __del__(self):
        self.csvfile.close()

if __name__ == '__main__':
    SCODE = '418830'
    SCODE = '063800'
    for trecord in EPWdata(SCODE):
        print(trecord['utc_datetime']),
        print(trecord['DNI (W/m^2)']),
        print(trecord['GHI (W/m^2)'])
