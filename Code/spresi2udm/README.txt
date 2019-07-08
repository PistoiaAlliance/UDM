Sample Python code to convert a SPRESI RD file to the UDM format

Author: jarek.tomczak@pistoiaalliance.org
Date:   15 November 2018


Introduction
------------

This package contains Python 3 code used to convert a sample SPRESI RD file to
the UDM format 5.0 (Brooklyn).  The code was written for this particular
conversion and doesn't pretend to be generic to handle e.g. all variations of
existing RD files.


Contents
--------
ctutils.py    - utility functions to manipulate connection tables
rdfutils.py   - classes and functions for reading of RD files
                (V2000 only at the moment)
udm.py        - function for writing UDM XML content
spresi2udm.py - the main conversion script


Execution
---------
The script expects two arguments - the name of an input SPRESI RD file and
the name of the output XML file:
    python spresi2udm.py <input SPRESI RD file> <output UDM file>
for example
    python spresi2udm.py spresi-sample.rdf spresi.xml
