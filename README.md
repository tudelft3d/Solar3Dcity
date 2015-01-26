Solar3Dcity
===========

A simple utility to estimate the solar potential of building roof surface(s) from a 3D city model stored in CityGML.

![solar3dcity-header](http://3dgeoinfo.bk.tudelft.nl/biljecki/github/solar3dcity/ov-solar-nw-n-legend-logo-small.png)

The scripts compute the solar irradiation data thanks to the [solpy](https://github.com/nrcharles/solpy) library.

#### Please note that this is an experimental research software prototype under continuous development.

Introduction
---------------------

The estimation of the solar irradiation of roof surfaces is one of the prominent use-cases of 3D city models. This use-case is important for estimating the feasibility of installing a photovoltaic panel on a roof. Such estimations are usually done on a large-scale, e.g. on the area of a municipality. For instance, see [an example](http://www.sun-area.net/index.php?id=103) in Germany. Further, there are many academic articles that explore this topic.

Despite the popularity of this 3D use-case, there are two drawbacks:

+ the software packages are not available for free, and
+ utilities that support data stored in [CityGML](http://en.wikipedia.org/wiki/CityGML) are seldom.

I have created this utility to fill this gap. This experimental software prototype was developed as a part of my [PhD research](http://3dgeoinfo.bk.tudelft.nl/biljecki/phd.html).


Conditions for use
---------------------


This software is free to use. However, you are kindly requested to acknowledge the use of this software by citing it in a research paper you are writing, reports, and/or other applicable materials; and mentioning the [3D Geoinformation group at the Delft University of Technology](http://3dgeoinfo.bk.tudelft.nl/). A research paper is under submission, hence please contact me to give you a reference to cite.

Further, I will be very happy to hear if you find this tool useful for your workflow. If you find it useful and/or have suggestions for its improvement, please let me know. Further, I am maintaining a list of users that I notify of corrections and updates.


### Academic reference with a detailed methodology

Coming soon. Journal paper under submission.


Estimating the solar irradiation: a quick introduction
---------------------

This short section gives an overview of the estimation of the solar irradiation, for understanding how the utility works.

The solar irradiation is the amount of solar energy received over a given time (e.g. one year) on an area (e.g. one metre squared). Contemporary solar panels are able to utilise 10-15% of this energy and convert it to electric energy.

### The three components of solar radiation

The solar radiation is composed of [three components](http://www.ftexploring.com/solar-energy/direct-and-diffuse-radiation.htm):

+ Direct radiation--the unobstructed radiation that reaches the surface directly.
+ [Diffuse radiation](http://en.wikipedia.org/wiki/Diffuse_sky_radiation)--the solar radiation scattered in the atmosphere (e.g. clouds). There are many empirical models to estimate the diffuse radiation.
+ Reflected radiation--the fraction of the solar radiation that is reflected, e.g. from the ground.

The global solar radiation is the sum of these three components.

### Cloud cover and weather

Clouds have a significant influence on the radiation. Therefore it is important to know the weather conditions on a location in order to account the estimation. For this, historic data is usually used.

### The yearly irradiation on a surface

The magnitude of the three radiation components is different depending on the day and time (i.e. position of the sun). Hence, the yearly irradiation is computed by integrating the magnitudes over the year, i.e. estimating the irradiation for many epochs during the year and summing them up (e.g. every 1 hour for every day).

### Tilted and oriented surfaces

The solar radiation differs depending on the tilt and orientation of a surface. The plot below show that TOF  (tilt-orientation-factors) for Delft in the Netherlands. It is visible that the difference between the irradiation on differently tilted and oriented surfaces is significant.

![TOF-plot](http://3dgeoinfo.bk.tudelft.nl/biljecki/github/solar3dcity/TOF-plot.png)

### Summing it up

The global solar irradiation on a tilted and oriented surface at location can be estimated from the following components of the surface:

+ location
+ tilt (of the normal)
+ orientation (azimuth)
+ historical weather (cloud) data

The annual irradiation is expressed in kWh/m^2. If the area of the surface is available, the normalised irradiation is multiplied with the surface area in order to obtain the irradiation in kWh.


### The role of 3D city models

3D city models are very important for the following reasons:

+ it is possible to extract the tilt and orientation of the normal of each roof surface,
+ it is possible to estimate the area of each roof surface,
+ the location of a building is available.

This is precisely what these scripts utilise.


System requirements
---------------------

Python packages:

+ [Numpy](http://docs.scipy.org/doc/numpy/user/install.html) (likely already on your system)
+ [lxml](http://lxml.de)
+ [solpy](https://github.com/nrcharles/solpy) - python library to model solar system power performance similar to PVWatts or NREL's System Advisor Model(SAM)
+ [caelum](https://github.com/nrcharles/caelum) - python library wrapper for various typical historical weather sources
+ Pickle

Optional:

+ matplotlib


### OS and Python version
  
The software has been developed on Mac OSX in Python 2.7, and has not been tested with other configurations. Hence, it is possible that some of the functions will not work on Windows and on Python 3.

Prerequisites
---------------------

+ All your polygons and buildings must have gml:ids, e.g.:

```
<bldg:Building gml:id="080a3632-c2b3-4488-945e-09701513f98d">
<gml:Polygon gml:id="6a37401c-d150-4c7c-a895-f02a72cf313d">
```


Overview of the workflow and advantages
---------------------

The utility does the following:

+ reads the CityGML file and extracts the roof surfaces for each building 
+ computes the tilt, area, and orientation for each roof surface
+ estimates the yearly solar irradiation thanks to the [solpy](https://github.com/nrcharles/solpy) library and EPW weather data (thanks to the [caelum](https://github.com/nrcharles/caelum) library)
+ writes the data back in the CityGML file

It is important to note the following:

+ The utility supports LOD3 models, for accounting the holes in the roof surfaces.
+ The weather and other data is loaded in the EnergyPlus weather file format (EPW), which is downloaded automatically.



Usage and options
---------------------
The code is composed of multiple Python files. Please follow these steps.

### Modify the parametres in the code

There are some parametres that need to be modified prior to running the code.

1. Open the `irr.py`, scroll to the end, and for the variable `STATION_CODE` put the code of the nearest weather station to your location. This can be found [here](http://apps1.eere.energy.gov/buildings/energyplus/weatherdata_about.cfm).
2. In `Solar3Dcity.py` go to line 196 and manually change the latitude and longitude of the area.
3. In `eree.py` go to line 19 and change the time zone.

Without these changes, the code will give wrong estimates. I plan to automate this in future work.


### (Optional:) Compute the TOFs to optimise the estimations


In case you have a large dataset (>1000 buildings), it is advised that first you compute the tilt-orientation factors. Then the software samples and interpolates the value of the yearly irradiation directly from this precomputed dataset. This is done with the `TOF.py` script.

```
python TOF.py -lat 52.01 -lon 4.36 -s 5
```

where -lat and -long are the latitude and the longitude of the location of your models (it is not extracted from them), and -s the *resolution* of the computations in degrees. The smaller the value, the better the estimation. If you have time put this to 1, if not put to 10.

Here are some examples of how much time it takes my computer to precompute the TOFs depending on the resolution:

| Resolution [degree] 	| Time       	|
|------------	|------------	|
| 15         	| 3 min      	|
| 10         	| 7 min      	|
| 5          	| 28 min     	|
| 2          	| 2 h 41 min 	|
| 1          	| 11 h       	|

The TOF will be saved as a file `TOF.dict` in the same directory. The code will then sample the irradiation directly from the precomputed values, saving you a lot of time.

If you toggle the `-p` option at the end you will get the plot as the one above.

```
python TOF.py -lat 52.01 -lon 4.36 -s 15 -p True
```

If you have precomputed the factors, and you just want to plot them run the following:

```
python TOF.py -lat 52.01 -lon 4.36 -s 15 -p True -f TOF.dict
```

The Perez et al. (1990) empirical model is used for the estimations.

### The main part: Estimate the solar irradiation of CityGML buildings

Put your CityGML file(s) in a separate directory. If you have precomputed the TOFs, run this:


```
python Solar3Dcity.py -i /path/to/CityGML/files/ -o /path/to/new/CityGML/files/ -f /path/to/the/TOF.dict
```

The tool will run the analysis on all `*.gml` it finds in that folder. The new files with the information on the solar irradiation of the building and its roof surface(s) will have the extension `-solar.gml`. That's it.

If you have not precomputed the TOFs, run this instead:

```
python Solar3Dcity.py -i /path/to/CityGML/files/ -o /path/to/new/CityGML/files/
```

to obtain the same result.

Please note that this will increase the computational time, as shown in the following table.

##### Processing times per average building

| Level of detail | Without precomputed TOF [sec] | With loaded TOF [sec] | Faster by |
|-----------------|-------------------------------|-----------------------|-----------|
| LOD2            |              3.20             |          0.02         | 160x      |
| LOD3            |              5.95             |          0.06         | 100x      |

Hence, if you have a large dataset, you might want to precompute the tilt-orientation factors.



### Extra: plot the daily clear-sky radiation

This is not really a part of the utility, but might be helpful to understand how the estimation of the solar irradiation works. The script `dailyplot.py` plots the global solar irradiance on a tilted and oriented surface at a location on a specific date. Multiple locations, multiple surfaces, and multiple dates are possible in order to compare the settings.

Go through the code to adjust the settings and then simply run:

```
python dailyplot.py
```

You will get something like this:

![Daily-plot](http://3dgeoinfo.bk.tudelft.nl/biljecki/github/solar3dcity/solar-dailyplot.png)

This is the magnitude of the irradiation during the day. Solar3Dcity integrates these values over the year in order to estimate the yearly irradiation.



Known issues and limitations
---------------------

It is important to note that this is an experimental research software. This means that it is not user-friendly, it has some limitations, and I cannot provide extensive support.

### Shadowing

Solar3Dcity does not estimate the shadowing from other objects (e.g. other buildings, chimneys, dormers, ...), which might be severe. This was out of scope of this work. If you have a suggestion how to efficiently implement this feature without sleepless weekends, please let me know.

### CityGML issues

The input/output files are read/stored in CityGML 2.0. Support for legacy versions 0.4 and 1.0 is not available.

### Python issues

This software has been programmed with Python 2.7. Version 3 is not supported.

### Geometric and coordinate issues

+ The program is known to crash in peculiar situations, e.g. when the geometry is invalid. For instance, a polygon is not planar. Please check your data.
+ The utility supports only local coordinate systems.
+ The utility is not extracting the latitude and longitude of a building, they have to be input manually.

### Multi-LOD files

Please do not use CityGML files with more than one LOD because the utility does not split between representations. However, multi-LOD files are seldom, so this should not be a problem.

### Schema (and ADE)

The results of the computations are added directly to the `<gml:Polygon>` and `<bldg:Building>` level. I am aware that this does not conform to CityGML. I did not have time yet to make an ADE or to store the data as generic attributes.

Visualisation possibilities
---------------------

This utility stores the data of the solar estimations directly in the CityGML file. However, data can be visualised by converting this to an enhanced OBJ with my utility [CityGML2OBJs](https://github.com/tudelft3d/CityGML2OBJs). An example is shown in the beginning of this file and here below.

![Daily-plot](http://3dgeoinfo.bk.tudelft.nl/biljecki/github/solar3dcity/zoom-solar-nw-legend-small.png)


Contact me for questions and feedback
---------------------
Filip Biljecki

[3D Geoinformation Research Group](http://3dgeoinfo.bk.tudelft.nl/)

Faculty of Architecture and the Built Environment

Delft University of Technology

email: fbiljecki at gmail dot com

[Personal webpage](http://3dgeoinfo.bk.tudelft.nl/biljecki/)


Acknowledgments
---------------------

+ This research is supported by the Dutch Technology Foundation STW, which is part of the Netherlands Organisation for Scientific Research (NWO), and which is partly funded by the Ministry of Economic Affairs. (Project code: 11300)

+ [Nathan Charles](https://github.com/nrcharles), the author of the [Solpy](https://github.com/nrcharles/solpy) and [Caelum](https://github.com/nrcharles/caelum) Python libraries, on which this package relies. Nathan promptly answered my questions and gave suggestions. Thank you.

+ People who gave suggestions and reported errors.

References and further reading
---------------------

+ [Placeholder for my journal paper (coming soon, I hope)]
+ Perez, R. et al., 1990. Modeling daylight availability and irradiance components from direct and global irradiance. Solar Energy, 44(5), pp. 271–289.
+ Hofierka, J. & Zlocha, M., 2012. A New 3-D Solar Radiation Model for 3-D City Models. Transactions in GIS, 16(5), pp. 681–690.
+ Šúri, M. et al., 2007. Potential of solar electricity generation in the European Union member states and candidate countries. Solar Energy, 81(10), pp. 1295–1305.
+ Freitas, S. et al., 2015. Modelling solar potential in the urban environment: State-of-the-art review. Renewable and Sustainable Energy Reviews, 41, pp. 915–931.