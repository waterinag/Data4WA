# This script download the Annual ETg and ETb raster maps; data available 2018-2025

import os
import numpy as np
import rasterio
from osgeo import gdal
import geopandas as gpd
from shapely.geometry import box

first_year = 2018
last_year = 2019


dataset=['ETb_WaPORv3','ETg_WaPORv3']

output_folder_path = ""   
geojson_boundary = "/Users/amanchaudhary/Documents/Resources/World_Bank/CongoBasin/shapefiles/CongoBasin.geojson" 




for data in dataset:
    output_folder = os.path.join(output_folder_path, f"{data}") 
    os.makedirs(output_folder, exist_ok=True)
    filenames = []

    for year in range(first_year, last_year + 1):
        url = f"https://wbwaterinfo.hel1.your-objectstorage.com/{data}_{year}.tif"
        output_filename = f"{data}_{year}.tif"
        filenames.append((url, output_filename))

        
    total = len(filenames)
    print("Total files:",total)

    for url, output_filename in filenames:

        output_path = os.path.join(output_folder, output_filename)
        # Skip if already processed
        if os.path.exists(output_path):
            print(f"✅ {output_filename} already exists, skipping...")
            continue

        # Remote file URL via /vsicurl/
        vsicurl_url = f"/vsicurl/{url}"

        print(f"Downloading...{output_filename}")

        try:
            warp_options = gdal.WarpOptions(
                cutlineDSName=geojson_boundary,
                cropToCutline=True,
                dstNodata=-9999
            )
            gdal.Warp(destNameOrDestDS=output_path, srcDSOrSrcDSTab=vsicurl_url, options=warp_options)
        except Exception as e:
            print(f"❌ GDAL warp failed for {output_filename}: {e}")
            continue

