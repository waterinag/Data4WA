import os
import numpy as np
import rasterio
from osgeo import gdal
import geopandas as gpd
from shapely.geometry import box


firstyear = 2009
lastyear = 2022

temporal_resolution="Annual" # Annual
output_folder = "/Users/amanchaudhary/Documents/Resources/World_Bank/Zambia/WaPOR_v2_L2_LULC_A"
geojson_boundary = "/Users/amanchaudhary/Documents/Resources/World_Bank/Zambia/Shapefile/Zambia_L0.geojson"



def check_extent(geojson_path, dataset_extent):
    try:
        gdf = gpd.read_file(geojson_path)
        aoi_bounds = gdf.total_bounds  # [minx, miny, maxx, maxy]

        dataset_bbox = box(*dataset_extent)
        aoi_bbox = box(*aoi_bounds)

        if not dataset_bbox.intersects(aoi_bbox):
            return "outside", aoi_bounds, dataset_extent
        elif not dataset_bbox.contains(aoi_bbox):
            return "partial", aoi_bounds, dataset_extent
        else:
            return "inside", aoi_bounds, dataset_extent
    except Exception:
        return None, None, None

L2_extent = [-30.0044643, -40.0044644, 65.0044644, 40.0044643]

status, aoi_bounds, dataset_extent = check_extent(geojson_boundary, L2_extent)
print(f"L2 Extent check: {status}")
print(f"AOI bounds: {aoi_bounds}")
print(f"Dataset extent: {dataset_extent}")


os.makedirs(output_folder, exist_ok=True)


filenames = []
if temporal_resolution == "Annual":
    for year in range(firstyear, lastyear + 1):

        url = f"https://storage.googleapis.com/fao-gismgr-wapor-2-data/DATA/WAPOR-2/MAPSET/L2-LCC-A/WAPOR-2.L2-LCC-A.{year}.tif"
        output_filename = f"wapor2_LULC_{year}.tif"
        filenames.append((url, output_filename))

else:
    raise ValueError("temporal_resolution must be 'Annual'")

total = len(filenames)
print("Total files:",total)


for url, output_filename in filenames:

    output_path = os.path.join(output_folder, output_filename)
    vsicurl_url = f"/vsicurl/{url}"



    # Skip if already processed
    if os.path.exists(output_path):
        print(f"✅ {output_filename} already exists, skipping...")
        continue


    try:
        print(f"Downloading {output_filename}")
        warp_options = gdal.WarpOptions(
            cutlineDSName=geojson_boundary,
            cropToCutline=True,
            dstNodata=-9999
        )
        gdal.Warp(destNameOrDestDS=output_path, srcDSOrSrcDSTab=vsicurl_url, options=warp_options)
    except Exception as e:
        print(f"❌ GDAL warp failed for {output_filename}: {e}")
        continue
