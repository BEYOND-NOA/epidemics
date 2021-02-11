import os
import re
import json
import uuid
import yaml
import datetime
import subprocess
import configparser
import rasterio as rs

#Select a product from the following:Sentinel2,Landsat7,Landsat8,Modis,Aspect,DEM,Slope
product = 'Sentinel2'
filePaths = []

config = configparser.RawConfigParser()
config.read("settings/settings.ini")

configInstrument = config[product]["instrument"]
configPlatform = config[product]["platform"]
configProductType = config[product]["productType"]

configCommand = config[product]["command"]
configPath = config[product]["path"]
configTemplate = config[product]["template"]

configOutputFilePath = config[product]["outputFilePath"]

# open the yaml template file by calling open(file)
# parse the previous result returning a dictionary by calling yaml.load
yamlTemplate = yaml.safe_load(open(configTemplate))

# get filePaths
for file in os.listdir(configPath):
    filepath = os.path.join(configPath, file)
    filePaths.append(filepath)

# iterate filePaths
for filepath in filePaths:
    baseName = os.path.basename(filepath)
    splitted = baseName.split("_")
    acquisitionDate = splitted[2]

    print("filepath", filepath)
    print("basename", baseName)
    # execute the command on the terminal
    dataset = rs.open(filepath)

    coordinateSystem = dataset.gcps[1].wkt

    #coordinates = jsonFormatted["cornerCoordinates"]
    lowerLeft = (dataset.bounds.bottom,dataset.bounds.left)#coordinates.get("lowerLeft")
    upperLeft = (dataset.bounds.top,dataset.bounds.left)#coordinates.get("upperLeft")
    lowerRight = (dataset.bounds.bottom,dataset.bounds.right)#coordinates.get("lowerRight")
    upperRight = (dataset.bounds.top,dataset.bounds.right)#coordinates.get("upperRight")

    # 'creation_dt', 'extent', 'format', 'grid_spatial', 'id', 'image', 'instrument', 'platform', 'processing_level', 'product_type"
    yamlTemplate["acquisition"]["groundstation"]["code"] = configInstrument
    # -------------------------
    yamlTemplate["creation_dt"] = datetime.datetime.strptime(acquisitionDate, "%Y-%m-%d").strftime("%Y-%m-%dT%H:%M:%S.%f")
    # -------------------------
    yamlTemplate["extent"]["center_dt"] = datetime.datetime.strptime(acquisitionDate, "%Y-%m-%d").strftime("%Y-%m-%dT%H:%M:%S.%f")
    yamlTemplate["extent"]["coord"]["ll"]["lat"] = lowerLeft[0]
    yamlTemplate["extent"]["coord"]["ll"]["lon"] = lowerLeft[1]

    yamlTemplate["extent"]["coord"]["lr"]["lat"] = lowerRight[0]
    yamlTemplate["extent"]["coord"]["lr"]["lon"] = lowerRight[1]

    yamlTemplate["extent"]["coord"]["ul"]["lat"] = upperLeft[0]
    yamlTemplate["extent"]["coord"]["ul"]["lon"] = upperLeft[1]

    yamlTemplate["extent"]["coord"]["ur"]["lat"] = upperRight[0]
    yamlTemplate["extent"]["coord"]["ur"]["lon"] = upperRight[1]
    # --------------------------------
    yamlTemplate["format"]["name"] = 'GeoTIFF'
    # --------------------------------
    yamlTemplate["grid_spatial"]["projection"]["geo_ref_points"]["ll"]["x"] = lowerLeft[1]
    yamlTemplate["grid_spatial"]["projection"]["geo_ref_points"]["ll"]["y"] = lowerLeft[0]

    yamlTemplate["grid_spatial"]["projection"]["geo_ref_points"]["lr"]["x"] = lowerRight[1]
    yamlTemplate["grid_spatial"]["projection"]["geo_ref_points"]["lr"]["y"] = lowerRight[0]

    yamlTemplate["grid_spatial"]["projection"]["geo_ref_points"]["ul"]["x"] = upperLeft[1]
    yamlTemplate["grid_spatial"]["projection"]["geo_ref_points"]["ul"]["y"] = upperLeft[0]

    yamlTemplate["grid_spatial"]["projection"]["geo_ref_points"]["ur"]["x"] = upperRight[1]
    yamlTemplate["grid_spatial"]["projection"]["geo_ref_points"]["ur"]["y"] = upperRight[0]

    yamlTemplate["grid_spatial"]["projection"]["spatial_reference"] = coordinateSystem
    # --------------------------------
    yamlTemplate["id"] = str(uuid.uuid4())
    # ------------------------

    for band in list(dataset.descriptions):
        yamlTemplate["image"]["bands"][band]["path"] = baseName

    print("configInstrument", configInstrument)
    print("configPlatform", configPlatform)
    print("configOutputFilePath", configOutputFilePath)
    # -------------------------
    yamlTemplate["instrument"]["name"] = configInstrument
    # -------------------------
    yamlTemplate["platform"]["code"] = configPlatform
    # ------------------------------------
    yamlTemplate["product_type"] = configProductType

    print("configOutputFilePath", configOutputFilePath)
    print("baseName", baseName)

    with open(configOutputFilePath+product+"_.yaml", "w") as file:
        documents = yaml.dump(yamlTemplate, file, default_flow_style=False, default_style=None, sort_keys=False)  # block style
    cmd_b = 'datacube -v dataset add '+configOutputFilePath+product+'.yaml'
    os.system(cmd_b)

