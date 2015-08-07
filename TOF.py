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

import cPickle as pickle
import irr
import argparse
import numpy as np

#-- Parse command-line arguments
PARSER = argparse.ArgumentParser(description='Estimate the tilt and orientation factor (TOF) for the annual insolation.')
PARSER.add_argument('-lat', '--latitude',
	help='latitude of the place', required=False)
PARSER.add_argument('-lon', '--longitude',
	help='longitude of the place', required=False)
PARSER.add_argument('-f', '--factors',
	help='Load the TOF if previously precomputed', required=False)
PARSER.add_argument('-s', '--step',
	help='Resolution of the computations.', required=False)
PARSER.add_argument('-p', '--plot',
    help='Plot the TOFs.', required=False)

def argRead(ar, default=None):
    """Corrects the argument input in case it is not in the format True/False."""
    if ar == "0" or ar == "False":
        ar = False
    elif ar == "1" or ar == "True":
        ar = True
    elif ar is None:
        if default:
            ar = default
        else:
            ar = False
    else:
        raise ValueError("Argument value not recognised.")
    return ar

ARGS = vars(PARSER.parse_args())
LATITUDE = ARGS['latitude']
LONGITUDE = ARGS['longitude']
FACTORS = ARGS['factors']
STEP = ARGS['step']
PLOT = argRead(ARGS['plot'], False)

#-- Place [lat, lon]
if LATITUDE and LONGITUDE:
	PLACE = (float(LATITUDE), float(LONGITUDE))
else:
	PLACE = (52.01, 4.36)

#-- Load the pre-computed TOF dictionary
if not FACTORS:
	loadDict = False
else:
	loadDict = True

#-- Azimuth-tilt-step in degrees
if STEP:
	STEP = float(STEP)
else:
	STEP = 15.0

asteps = int(360.0 / STEP)
tsteps = int(90.0 / STEP)
azimuths = np.linspace(0.0, 360.0, asteps + 1)
tilts = np.linspace(0.0, 90.0, tsteps + 1)

#-- If the TOFs are already precomputed
if loadDict:
    with open(FACTORS, "rb") as myFile:
        TOF = pickle.load(myFile)

else:
	#-- Create the dictionary
    TOF = {}

    #-- For each azimuth
    for az in azimuths:

    	#-- Open a sub-dictionary
        TOF[str(az)] = {}

        #-- For each tilt
        for tr in tilts:
        	#-- Get the total yearly solar irradiation
            total = irr.yearly_total_irr(PLACE, az, tr)#, INTERVAL, cloud_cover)
            #-- Store it in the dictionary
            TOF[str(az)][str(tr)] = total
            #-- Print the progress
            print "Azimuth:", az, "\tTilt:", tr, "\tIrradiation:", total, "kWh/m^2"

    #-- Store the obtained values to save time later
    if TOF:
        with open('TOF.dict', 'wb') as dict_items_save:
            pickle.dump(TOF, dict_items_save)


if PLOT:
    #-- Plotting time!
    import matplotlib as mpl
    #from matplotlib import rc
    import matplotlib.pyplot as plt
    import matplotlib.mlab as ml

    plt.rc('text', usetex=True)
    plt.rc('font', family='serif')

    #-- Organise the data for plotting
    irrTOFa = []
    irrTOFt = []
    irrTOFi = []
    for azimuth in TOF:
        for tilt in TOF[azimuth]:
            radiationAmount = TOF[azimuth][tilt]
            irrTOFa.append(azimuth)
            irrTOFt.append(tilt)
            irrTOFi.append(radiationAmount)

    #-- First figure (with 90-270 azimuths)
    fig1 = plt.figure(1)


    xi = np.linspace(90, 270, 180)
    yi = np.linspace(0, 90, 90)
    zi = ml.griddata(irrTOFa, irrTOFt, irrTOFi, xi, yi, interp='nn') # linear interpolation does not work, so natural neighbour is used

    vmin = 600.0
    vmax = 1250.0

    import seaborn as sns
    sns.set(style="white", font='serif', rc={'axes.facecolor': '#FFFFFF', 'grid.linestyle': '', 'axes.grid' : False, 'font.family': ['serif'], 'legend.frameon': True})

    origin = 'lower'
    cmap = plt.cm.get_cmap("afmhot")# Blues
    CSF = plt.contourf(xi, yi, zi, 25, cmap=cmap, origin=origin, vmin=vmin, vmax=vmax)#, 15, linewidths = 0.5, colors = 'k')
    CS = plt.contour(xi, yi, zi, 25, origin=origin, linewidths=.25, colors='k')
    plt.axes().set_aspect('equal') # ,'datalim'
    plt.xticks(np.arange(90.0, 270.01, 10.0))
    plt.tick_params(axis='both', which='major', labelsize=9)
    plt.clabel(CS, inline=1, fontsize=7, colors='k', fmt='%1.0f') #CS.levels[::2],
    plt.xlim(90, 270)
    plt.ylim(0, 90)

    ttl = r"Global solar irradiation on a tilted and oriented surface"
    ttl += "\n"
    ttl += r"in Delft, the Netherlands (N52.01$^{\circ}$, E4.36$^{\circ}$)"
    xl = r"Azimuth [$^{\circ}$]"
    yl = r"Tilt [$^{\circ}$]"
    cbtl = r"Annual solar irradiation [kWh/m$^{2}$/yr]"
    plt.title(ttl, fontsize=12)
    plt.xlabel(xl, fontsize=11)
    plt.ylabel(yl, fontsize=11)
    cbar = plt.colorbar(CSF, shrink=0.55)
    cbar.ax.set_ylabel(cbtl, fontsize=11)
    # labels = [item.get_text() for item in CS.ax.get_xticklabels()]
    # print labels
    # labels = [item.get_text() for item in plt.axes().get_xticklabels()]
    # print labels
    # labels = [item.get_text() for item in CSF.ax.get_xticklabels()]
    # print labels
    # labels[0] = str(labels[-1]) + '\n' + 'E'
    # labels[-1] = str(labels[-1]) + '\n' + 'W'
    # CS.ax.set_xticklabels(labels)
    plt.savefig('TOF-plot.pdf', bbox_inches='tight')
    plt.show()

    # #-- Second figure (with 0-360 azimuths)
    # plt.figure(2)

    # xi = np.linspace(0, 360, 360)
    # yi = np.linspace(0, 90, 90)
    # zi = ml.griddata(irrTOFa, irrTOFt, irrTOFi, xi, yi)

    # CS = plt.contour(xi, yi, zi, 20)#, 15, linewidths = 0.5, colors = 'k')
    # plt.axes().set_aspect('equal') # ,'datalim'
    # plt.xticks(np.arange(0, 360, 25.0))
    # plt.clabel(CS, inline=3, fontsize=10, fmt='%1.0f')
    # plt.xlim(0, 360)
    # plt.ylim(0, 90)
    # plt.title(ttl, fontsize=14)
    # plt.xlabel(xl, fontsize=12)
    # plt.ylabel(yl, fontsize=12)
    # plt.savefig('TOF-plot-360.pdf', bbox_inches='tight')
    # plt.show()