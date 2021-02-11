# coding=utf-8
"""
Ingest data from the command-line.
"""
from __future__ import absolute_import, division

import yaml
import uuid
import logging
from xml.etree import ElementTree
from pathlib import Path
import yaml
import click
from osgeo import gdal, osr
from dateutil import parser
import os
import sys


def main(input):
    #print(input)
#    os.chdir('/datacube/original_data/temperature')
#    os.chdir('/datacube/original_data/rain')
    os.chdir('/datacube/original_data/wind')
    path = input

    #ds = gdal.Open(str(path))

#    with open ("index_temp_grib_tiff_2.yaml", 'r') as file:
    with open("index_wind_v_grib_tiff_2.yaml", 'r') as file:
        documents = yaml.load(file, Loader=yaml.FullLoader)
        #for item, doc in documents.items():
            #print(item, ":", doc)
        yourdate = parser.parse(path[5:15])
        iso_date = yourdate.isoformat()

        documents['creation_dt'] = iso_date
        documents['extent']['center_dt'] =iso_date
        documents['extent']['from_dt'] =iso_date
        documents['extent']['to_dt'] =iso_date
        documents['id'] =  str(uuid.uuid4())

        print(documents['image'])
        for dict in documents['image']['bands']:
            documents['image']['bands'][dict]['path'] = path
            #print(dict)
#        with open ("index_temp_grib_tiff_2.yaml", 'w') as file:
#            yaml.dump(documents,file)
        with open("index_wind_v_grib_tiff_2.yaml", 'w') as file:
            yaml.dump(documents,file)


if __name__ == "__main__":
    main(sys.argv[1])
