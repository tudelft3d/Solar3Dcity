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
import datetime

settings = []

place = (52.01, 4.36)

tzoffset = datetime.timedelta(hours=2)

settings.append({'Name' : 'Surface A',
'Tilt' : 40.0,
'Azimuth' : 180.0,
})

settings.append({'Name' : 'Surface B',
'Tilt' : 40.0,
'Azimuth' : 90.0,
})

#-- Which days
#-- month, day format
epochs = [[3, 27], [6, 21]]

#-- Sampling interval
interval = 5

#-- Results
res = {}

#-- Clouds: left for future work, at this moment the computations are clear-sky
ccddatabase = None

#-- Iterate the days
for epoch in epochs:

    month = epoch[0]
    day = epoch[1]

    d = datetime.date(2015, month, day)
    #-- Tweaking to get the proper key values for dates
    if month < 10:
        m_s = '0' + str(month)
    else:
        m_s = str(month)
    if day < 10:
        d_s = '0' + str(day)
    else:
        d_s = str(day)
    #-- These are UTC times. The program is not smart enough to use sunrise and sunset times, but this works too
    for hour in range(3, 20):
        for minute in range(0, 60, interval):
            #-- Datetime
            t = datetime.time(hour, minute)
            dt = datetime.datetime.combine(d, t)

            #-- Get the historic cloud cover for that day
            # if ccddatabase:
            #     cloud_cover = ccddatabase[str(m_s)+str(d_s)]
            # else:
            #     cloud_cover = 0.0

            for setting in settings:
                if setting['Name'] not in res:
                    res[setting['Name']] = {}
                e = str(m_s)+str(d_s)
                if e not in res[setting['Name']]:
                    res[setting['Name']][e] = []

                #-- Global synthetic irradiation from Solpy
                global_irradiation_rec = irradiation.blave(dt, place, 0, 180)
                #-- Adjust it for the tilt. The value is now in W/m^2
                irrValue = irradiation.irradiation(global_irradiation_rec, place, None, setting['Tilt'], setting['Azimuth'], 'p9')
                horr_irrValue = irradiation.irradiation(global_irradiation_rec, place, None, 0, 180, 'p9')
                #-- Workaround to keep the data aligned
                d_ = datetime.date(2013, 1, 1)
                t_ = datetime.time(hour, minute)
                dt_ = datetime.datetime.combine(d_, t_)
                res[setting['Name']][e].append([dt_, irrValue, horr_irrValue])

import scipy
import os
#-- Fix LaTeX for macOS 10.12
os.environ['PATH'] = os.environ['PATH'] + ':/Library/TeX/texbin'
import matplotlib as mpl
mpl.use('TkAgg')
import matplotlib.pyplot as plt
plt.rc('text', usetex=True)
plt.rc('font', family='serif')
import seaborn as sns
#-- Plotting properties
sns.set(style="white", font='serif', rc={'axes.facecolor': '#FFFFFF', 'grid.linestyle': '', 'axes.grid' : False, 'font.family': ['serif'], 'legend.frameon': True})
colors = sns.color_palette()

# fig = plt.figure(1)
fig, ax1 = plt.subplots(figsize=(8, 4))
timestamp = []
total_ir = []
total_ir_h = []

for v in res['Surface A']['0327']:
        timestamp.append(v[0] + tzoffset)
        total_ir.append(v[1])
        total_ir_h.append(v[2])

A_1 = plt.plot(timestamp, total_ir, color=colors[0], linestyle='--', marker='o', markevery=slice(60, 170, 15))

timestamp = []
total_ir = []
total_ir_h = []

for v in res['Surface B']['0327']:
        timestamp.append(v[0] + tzoffset)
        total_ir.append(v[1])
        total_ir_h.append(v[2])

B_1 = plt.plot(timestamp, total_ir, color=colors[1], linestyle='--', marker='v', markevery=slice(60, 170, 15))
# H_1 = plt.plot(timestamp, total_ir_h, color=colors[2], linestyle='--')


timestamp = []
total_ir = []
total_ir_h = []

for v in res['Surface A']['0621']:
        timestamp.append(v[0] + tzoffset)
        total_ir.append(v[1])
        total_ir_h.append(v[2])

A_2 = plt.plot(timestamp, total_ir, color=colors[0], linestyle='-', marker='o', markevery=slice(30, 185, 15))

timestamp = []
total_ir = []
total_ir_h = []

for v in res['Surface B']['0621']:
        timestamp.append(v[0] + tzoffset)
        total_ir.append(v[1])
        total_ir_h.append(v[2])

B_2 = plt.plot(timestamp, total_ir, color=colors[1], linestyle='-', marker='v', markevery=slice(30, 185, 15))
# H_2 = plt.plot(timestamp, total_ir_h, color=colors[2], linestyle='-')

ddd = scipy.zeros(len(total_ir_h))
#plt.fill_between(timestamp, total_ir_h, where=total_ir_h>=ddd, interpolate=True, color='k')

import matplotlib.dates as md
xfmt = md.DateFormatter('%H:%M')
ax1.xaxis.set_major_formatter(xfmt)

sns.despine(left=False, bottom=False)
# ax1.tick_params(axis='x', which='major', bottom='on')
# ax1.set_xlim([734869.16, 734869.84])
ax1.set_ylim([0, 1050])

# plt.title('Clear-sky global solar irradiance for Delft, the Netherlands', size=15)
plt.xlabel('Local time', size=14)
#plt.ylabel(u'Total solar irradiation (W/m²)', size=14)
plt.ylabel(r'Global solar irradiance (W/m$^{2}$)', size=14)
plt.legend(['A on 27 Mar', 'B on 27 Mar', 'A on 21 Jun', 'B on 21 Jun'], loc='upper center', bbox_to_anchor=(0.5, 1.15), fancybox=1, shadow=0, ncol=4, numpoints=1, prop={'size':12})
plt.savefig('dailyplot.png', bbox_inches='tight', dpi=300)
plt.savefig('dailyplot.pdf', bbox_inches='tight')
# plt.show()
