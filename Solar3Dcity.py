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

import polygon3dmodule
import markup3dmodule
from lxml import etree
import irr
import argparse
import glob
import os
import pickle
from scipy import interpolate
import numpy as np
import math

#-- Name spaces
ns_citygml = "http://www.opengis.net/citygml/2.0"

ns_gml = "http://www.opengis.net/gml"
ns_bldg = "http://www.opengis.net/citygml/building/2.0"
ns_xsi = "http://www.w3.org/2001/XMLSchema-instance"
ns_xAL = "urn:oasis:names:tc:ciq:xsdschema:xAL:2.0"
ns_xlink = "http://www.w3.org/1999/xlink"
ns_dem = "http://www.opengis.net/citygml/relief/2.0"

nsmap = {
    None : ns_citygml,
    'gml': ns_gml,
    'bldg': ns_bldg,
    'xsi' : ns_xsi,
    'xAL' : ns_xAL,
    'xlink' : ns_xlink,
    'dem' : ns_dem
}

#-- ARGUMENTS
# -i -- input directory (it will read ALL CityGML files in a directory)
# -o -- output directory (it will output the enriched CityGMLs in that directory with the naming convention Delft.gml becomes Delft-solar.gml)
# -f -- factors (precomputed tilt-orientation-factors)
PARSER = argparse.ArgumentParser(description='Calculate the yearly solar irradiation of roof surfaces.')
PARSER.add_argument('-i', '--directory',
    help='Directory containing CityGML file(s).', required=True)
PARSER.add_argument('-o', '--results',
    help='Directory where the enriched "solar" CityGML file(s) should be written.', required=True)
PARSER.add_argument('-f', '--factors',
    help='Load the TOF if previously precomputed', required=False)
ARGS = vars(PARSER.parse_args())
DIRECTORY = ARGS['directory']
RESULT = ARGS['results']
FACTORS = ARGS['factors']
#-- Load the pre-computed dictionary
if not FACTORS:
    loadDict = False
else:
    loadDict = True


#-- If the TOFs are already precomputed
if loadDict:
    with open(FACTORS, "rb") as myFile:
        TOF_strings = pickle.load(myFile)
    TOF = {}

    for azStr in TOF_strings:
        azFloat = round(float(azStr), 2)
        TOF[azFloat] = {}
        for tiStr in TOF_strings[azStr]:
            tiFloat = round(float(tiStr), 2)
            TOF[azFloat][tiFloat] = float(TOF_strings[azStr][tiStr])
    TS = sorted(TOF)
    res = TS[1]-TS[0]

else:
    pass#import knmicloud


def squareVerts(a,t,res):
    """Get the vertices of the interpolation square."""
    invRes = 1/res
    aB = math.trunc(a*invRes)/invRes
    aT = math.ceil(a*invRes)/invRes
    if aT == aB:
        aT += res#1.0
    tB = math.trunc(t*invRes)/invRes
    tT = math.ceil(t*invRes)/invRes
    if tT == tB:
        tT += res#1.0
    return [[aB, aT], [tB, tT]]


def bilinear_interpolation(x, y, points):
    # Function taken from http://stackoverflow.com/a/8662355/4443114
    '''Interpolate (x,y) from values associated with four points.

    The four points are a list of four triplets:  (x, y, value).
    The four points can be in any order.  They should form a rectangle.

        >>> bilinear_interpolation(12, 5.5,
        ...                        [(10, 4, 100),
        ...                         (20, 4, 200),
        ...                         (10, 6, 150),
        ...                         (20, 6, 300)])
        165.0

    '''
    # See formula at:  http://en.wikipedia.org/wiki/Bilinear_interpolation

    points = sorted(points)               # order points by x, then by y
    (x1, y1, q11), (_x1, y2, q12), (x2, _y1, q21), (_x2, _y2, q22) = points

    if x1 != _x1 or x2 != _x2 or y1 != _y1 or y2 != _y2:
        raise ValueError('points do not form a rectangle')
    if not x1 <= x <= x2 or not y1 <= y <= y2:
        raise ValueError('(x, y) not within the rectangle')

    return (q11 * (x2 - x) * (y2 - y) +
            q21 * (x - x1) * (y2 - y) +
            q12 * (x2 - x) * (y - y1) +
            q22 * (x - x1) * (y - y1)
           ) / ((x2 - x1) * (y2 - y1) + 0.0)


def interpolator(grid_subset, coord):
    """Bilinear interpolation of TOF values."""
    #-- Azimuths in the subset grid
    azG = np.array(grid_subset[0])
    tiG = np.array(grid_subset[1])
    values = []
    values.append((azG[0], tiG[1], TOF[azG[0]][tiG[1]]))
    values.append((azG[0], tiG[0], TOF[azG[0]][tiG[0]]))
    values.append((azG[1], tiG[1], TOF[azG[1]][tiG[1]]))
    values.append((azG[1], tiG[0], TOF[azG[1]][tiG[0]]))
    return bilinear_interpolation(coord[0], coord[1], values)

def irr_from_tof(tilt, azimuth):
    """Construct the square with four TOF values around the point for interpolation."""
    gs = squareVerts(azimuth,tilt,res)
    return interpolator(gs, [azimuth,tilt])


class Building(object):
    def __init__(self, xml, id):
        #-- ID of the building
        self.id = id
        #-- XML tree of the building
        self.xml = xml
        #-- Data for each roof surface required for the computation of the solar stuff
        self.roofdata = {}
        #-- List of IDs of openings, not to mess with usable roof surfaces
        self.listOfOpenings = []
        #-- Compute the total areas of surfaces per semantic class (not really required; reserved for future use)
        #-- RoofSurface
        self.RoofSurfaceArea = self.roofarea()
        #-- WallSurface
        self.WallSurfaceArea = self.wallarea()
        #-- GroundSurface
        self.GroundSurfaceArea = self.groundarea()
        #-- Openings
        self.OpeningArea = self.openingarea()
        #-- All surfaces (including openings)
        self.AllArea = self.allarea()
        #-- All surfaces without openings
        self.RealArea = self.AllArea - self.OpeningArea
        #-- Do the solar estimation
        self.solarinfo()

    def solarinfo(self):        
        """Computes the area, azimuth, and tilt for each roof surface (id compulsory)."""
        place = (52.01, 4.36)
        for roofsurface in self.roofsurfaces:
            #-- Skip the openings
            if roofsurface.attrib['{%s}id' %ns_gml] in self.listOfOpenings:
                continue
            #-- Add it to the list
            listofxmlroofsurfaces.append(roofsurface)
            #-- gml:id of the polygon
            pid = roofsurface.attrib['{%s}id' %ns_gml]
            #-- Area
            area = polygon3dmodule.getAreaOfGML(roofsurface, True)
            #-- Compute the normal
            norm = polygon3dmodule.getNormal(markup3dmodule.GMLpoints(markup3dmodule.polydecomposer(roofsurface)[0][0]))
            #-- Get the azimuth and tilt from the surface normal
            az, tilt = polygon3dmodule.getAngles(norm)
            az = round(az, 3)
            #-- 360 -> 0 degrees
            if az == 360.0:
                az = 0.0
            tilt = round(tilt, 3)
            #-- Peculiar problems with the normals, with a cheap solution. Luckily very uncommon.
            if tilt == 180:
                tilt = 0.0
            if tilt >= 180:
                tilt = tilt - 180.01
            elif tilt > 90:
                tilt = tilt - 90.01
            elif tilt == 90:
                tilt = 89.9
            #-- Flat surfaces always have the azimuth zero
            if tilt == 0.0:
                az = 0.0
            #-- If the TOF file is loaded, sample the irradiance
            if loadDict:
                irradiation = irr_from_tof(tilt, az)
            #-- If the TOF file is not loaded, estimate the values
            else:
                irradiation = irr.yearly_total_irr(place, az, tilt)
            #-- Add the values
            self.roofdata[pid] = {'area' : area, 'azimuth' : az, 'tilt' : tilt, 'irradiation' : irradiation, 'total_irradiation' : irradiation*area}
            roofsurfacedata[pid] = {'area' : area, 'azimuth' : az, 'tilt' : tilt, 'irradiation' : irradiation, 'total_irradiation' : irradiation*area}
            #self.roofdata.append([self.id, pid, area, az, tilt, irradiation, irradiation*area])
        self.sumIrr = 0
        #-- Sum the values for the building
        for rs in self.roofdata:
            self.sumIrr += self.roofdata[rs]['total_irradiation']

    def roofarea(self):
        """The total area of RoofSurface."""
        self.roofs = []
        self.roofsurfaces = []
        roofarea = 0.0
        openings = 0.0
        for child in self.xml.getiterator():
            if child.tag == '{%s}RoofSurface' %ns_bldg:
                self.roofs.append(child)
                openings += oparea(child)
        for surface in self.roofs:
            for w in surface.findall('.//{%s}Polygon' %ns_gml):
                self.roofsurfaces.append(w)
        for roofsurface in self.roofsurfaces:
            roofarea += polygon3dmodule.getAreaOfGML(roofsurface, True)
            #-- Compute the normal
            norm = polygon3dmodule.getNormal(markup3dmodule.GMLpoints(markup3dmodule.polydecomposer(roofsurface)[0][0]))
            polygon3dmodule.getAngles(norm)
        return roofarea - openings

    def wallarea(self):
        """The total area of WallSurfaces."""
        self.walls = []
        self.wallsurfaces = []
        wallarea = 0.0
        openings = 0.0
        #-- Account for openings
        for child in self.xml.getiterator():
            if child.tag == '{%s}WallSurface' %ns_bldg:
                self.walls.append(child)
                openings += oparea(child)
        for surface in self.walls:
            for w in surface.findall('.//{%s}Polygon' %ns_gml):
                self.wallsurfaces.append(w)
        for wallsurface in self.wallsurfaces:
            wallarea += polygon3dmodule.getAreaOfGML(wallsurface, True)
        return wallarea - openings

    def groundarea(self):
        """The total area of GroundSurfaces."""
        self.grounds = []
        groundarea = 0.0
        for child in self.xml.getiterator():
            if child.tag == '{%s}GroundSurface' %ns_bldg:
                self.grounds.append(child)
        self.count = 0
        for groundsurface in self.grounds:
            self.count += 1
            groundarea += polygon3dmodule.getAreaOfGML(groundsurface, True)
        return groundarea

    def openingarea(self):
        """The total area of Openings."""
        matching = []
        self.openings = []
        openingarea = 0.0
        for child in self.xml.getiterator():
            if child.tag == '{%s}opening' %ns_bldg:
                matching.append(child)
                #-- Store the list of openings
                for o in child.findall('.//{%s}Polygon' %ns_gml):
                    self.listOfOpenings.append(o.attrib['{%s}id' %ns_gml])
        for match in matching:
            for child in match.getiterator():
                if child.tag == '{%s}surfaceMember' %ns_gml:
                    self.openings.append(child)
        self.count = 0
        for openingsurface in self.openings:
            self.count += 1
            openingarea += polygon3dmodule.getAreaOfGML(openingsurface, True)
        return openingarea

    def allarea(self):
        """The total area of all surfaces."""
        self.allareas = []
        allarea = 0.0
        # for child in self.xml.getiterator():
        #   if child.tag == '{%s}surfaceMember' %ns_gml:
        #       self.allareas.append(child)
        self.allareas = self.xml.findall('.//{%s}Polygon' %ns_gml)
        self.count = 0
        for poly in self.allareas:
            self.count += 1
            allarea += polygon3dmodule.getAreaOfGML(poly, True)
        return allarea

def oparea(xmlelement):
    """The total area of Openings in the XML tree."""
    matching = []
    openings = []
    openingarea = 0.0
    for child in xmlelement.getiterator():
        if child.tag == '{%s}opening' %ns_bldg:
            #print 'opening'
            matching.append(child)
    for match in matching:
        for child in match.getiterator():
            if child.tag == '{%s}surfaceMember' %ns_gml:
                openings.append(child)
    for openingsurface in openings:
        openingarea += polygon3dmodule.getAreaOfGML(openingsurface, True)
    return openingarea  


print "I am Solar3Dcity. Let me search for your CityGML files..."

#-- Find all CityGML files in the directory
os.chdir(DIRECTORY)
for f in glob.glob("*.gml"):
    FILENAME = f[:f.rfind('.')]
    FULLPATH = DIRECTORY + f

    CITYGML = etree.parse(FULLPATH)
    root = CITYGML.getroot()
    cityObjects = []
    buildings = []

    listofxmlroofsurfaces = []
    roofsurfacedata = {}

    #-- Find all instances of cityObjectMember and put them in a list
    for obj in root.getiterator('{%s}cityObjectMember'% ns_citygml):
        cityObjects.append(obj)

    print FILENAME
    print "\tThere are", len(cityObjects), "cityObject(s) in this CityGML file"

    for cityObject in cityObjects:
        for child in cityObject.getchildren():
            if child.tag == '{%s}Building' %ns_bldg:
                buildings.append(child)

    #-- Store the buildings as classes
    buildingclasses = []
    for b in buildings:
        id = b.attrib['{%s}id' %ns_gml]
        buildingclasses.append(Building(b, id))

    print "\tI have read all buildings, now I will search for roofs and estimate their solar irradiation..."

    #-- Store the obtained data in a dictionary
    solardata = {}

    #-- Check if there are roof surfaces in the file
    rsc = 0

    #-- Iterate all buildings
    for bu in buildingclasses:
        solardata[bu.id] = {'roofarea' : bu.roofarea(), 'totalIrradiation' : bu.sumIrr}
        rsc += bu.RoofSurfaceArea

    if rsc > 0:

        print '\tEnriching CityGML file with the solar irradiation data...'

        for rsxml in listofxmlroofsurfaces:
            rsid = rsxml.attrib['{%s}id' %ns_gml]
            s = etree.SubElement(rsxml, "area")
            s.text = str(roofsurfacedata[rsid]['area'])
            s.attrib['unit'] = 'm^2'
            i = etree.SubElement(rsxml, "totalIrradiation")
            i.text = str(roofsurfacedata[rsid]['total_irradiation'])
            i.attrib['unit'] = 'kWh'
            a = etree.SubElement(rsxml, "azimuth")
            a.text = str(roofsurfacedata[rsid]['azimuth'])
            a.attrib['unit'] = 'degree'
            t = etree.SubElement(rsxml, "tilt")
            t.text = str(roofsurfacedata[rsid]['tilt'])
            t.attrib['unit'] = 'degree'
            ni = etree.SubElement(rsxml, "irradiation")
            ni.text = str(roofsurfacedata[rsid]['irradiation'])
            ni.attrib['unit'] = 'kWh/m^2'



        for b in buildings:
            bid = b.attrib['{%s}id' %ns_gml]
            s = etree.SubElement(b, "roofArea")
            s.text = str(solardata[bid]['roofarea'])
            s.attrib['unit'] = 'm^2'
            i = etree.SubElement(b, "yearlyIrradiation")
            i.text = str(solardata[bid]['totalIrradiation'])
            i.attrib['unit'] = 'kWh'


        os.chdir(RESULT)
        with open(RESULT + FILENAME + '-solar.gml', 'w') as f:
                f.write(etree.tostring(root))

        print "\tFile written."

    else:
        print "\tI am afraid I did not find any RoofSurface in your CityGML file."

print "All done."