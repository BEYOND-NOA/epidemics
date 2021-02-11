from os import listdir
import os
from os.path import isfile, join
import subprocess

#mypath = '/datacube/original_data/temperature'
#mypath = '/datacube/original_data/rain'
mypath = '/datacube/original_data/wind'

onlyfiles = [f for f in listdir(mypath) if isfile(join(mypath, f))]

suffix = '_2.tif'

for file in onlyfiles:
    if file.endswith(suffix):
        cmd_a = 'python /home/datacube-epidemics/Datacube/prepare_scripts/tiff_prepare_script.py %s' %(file)
        os.system(cmd_a)
        print('Preparing data...')
#        cmd_b = 'datacube -v dataset add /datacube/original_data/temperature/index_temp_grib_tiff_2.yaml'
#        cmd_b = 'datacube -v dataset add /datacube/original_data/rain/index_rain_grib_tiff_2.yaml'
        #cmd_b = 'datacube -v dataset add /datacube/original_data/wind/index_wind_u_grib_tiff_2.yaml'
        cmd_b = 'datacube -v dataset add /datacube/original_data/wind/index_wind_v_grib_tiff_2.yaml'
        os.system(cmd_b)
    else:
        print('SOMETHING IS WRONG')
