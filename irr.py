#!/usr/bin/python
# -*- coding: utf-8 -*-

# The MIT License (MIT)

# This code is part of the Solar3Dcity package

# Copyright (c) 2015 
# Filip Biljecki
# Delft University of Technology
# fbiljecki@gmail.com

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

from solpy import irradiation
from caelum import eere
# import eree
import datetime

def yearly_total_irr(place, az, tr): #, interval=30, ccd=None
    """Function which estimates the total irradiation.
    Input: location (lat, lon),
    az (azimuth in degrees, south is at 180 degrees),
    tr (tilt of the roof in degrees, flat roof is 0),
    #interval (what is the precision of the integration in minutes),
    #cloud cover data (dictionary with floats from 0 to 1, for each day of the year in mmdd format (e.g. '1231');
        get it from your local weather station).
    Returns total yearly irradiation for the tilted and oriented surface in kWh/m^2.
    """

    #-- Old method with KNMI data

    #-- Counter for the yearly irradiation in kWh/m^2
    # yearly_sum = 0

    # #-- Compute for all dates and times
    # for month in range(1, 13):
    #     for day in range(1, 32):
    #         #-- Skip these dates
    #         if (day == 29 or day == 30) and month == 2:
    #             continue
    #         if day == 31 and month in (2, 4, 6, 9, 11):
    #             continue

    #         #-- Daily value reset
    #         daily_rads = 0
    #         #-- Tweaking to get the proper key values for dates
    #         if month < 10:
    #             m_s = '0' + str(month)
    #         else:
    #             m_s = str(month)
    #         if day < 10:
    #             d_s = '0' + str(day)
    #         else:
    #             d_s = str(day)
    #         d = datetime.date(2013, month, day)
    #         #-- These are UTC times. The program is not smart enough to use sunrise and sunset times, but this works too
    #         for hour in range(3, 20):
    #             for minute in range(0, 60, interval):
    #                 #-- Datetime
    #                 t = datetime.time(hour, minute)
    #                 dt = datetime.datetime.combine(d, t)
    #                 #-- Get the historic cloud cover for that day
    #                 if ccd:
    #                     cloud_cover = ccd[str(m_s)+str(d_s)]
    #                 else:
    #                     cloud_cover = 0.0
    #                 #-- Global synthetic irradiation from Solpy
    #                 global_irradiation_rec = irradiation.blave(dt, place, 0, 180, cloud_cover)
    #                 #-- Adjust it for the tilt. The value is now in W/m^2
    #                 irrValue = irradiation.irradiation(global_irradiation_rec, place, None, tr, az, 'p9')

    #                 #-- Integrate the value over the time interval (get Wh/m^2) and convert it to kWh/m^2 and add it to the daily summed value
    #                 daily_rads += (irrValue * (float(interval)/60.0)) / 1000.0

    #         #-- When finished with the day, add the estimated value to the yearly sum
    #         yearly_sum += daily_rads



    #-- EPW Weather data
    STATION_CODE = '062400' # '062400' for Amsterdam
    #-- Fetch the dataset thanks to the caelum library
    records = eere.EPWdata(STATION_CODE)
    #-- Get the global yearly irradiance (Wh/m^2/year)
    TOTAL = sum([irradiation.irradiation(record=rec, location=place, horizon=None, t=tr, array_azimuth=az, model='p9') for rec in records])     
    #-- Divide it by 1000 to get the value in kWh/m^2/year
    yearly_sum = TOTAL/1000.

    #-- Yearly irradiation in kWh/m^2/year
    return yearly_sum