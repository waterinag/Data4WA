# Reference Evapotranspiration (RET) 
Reference evapotranspiration (RET) is defined as the evapotranspiration from a hypothetical reference crop. It simulates the behaviour of a well-watered grass surface and can be used to estimate potential ET for different crops by applying predefined crop coefficients. This information can be used in the design of irrigation schemes. 

For further information on the methodology read the WaPOR documentation available at: [https://bitbucket.org/cioapps/wapor-et-look/wiki/Home](https://bitbucket.org/cioapps/wapor-et-look/wiki/Home)

---


## Dataset Overview

- **Product**: WaPOR v3
- **Source**: [https://console.cloud.google.com/storage/browser/fao-gismgr-wapor-3-data/DATA/WAPOR-3/MAPSET](https://console.cloud.google.com/storage/browser/fao-gismgr-wapor-3-data/DATA/WAPOR-3/MAPSET)
- **Format**: GeoTIFF
- **Extent**: Global
- **Data Availability**: 2018 - present 
- **Spatial Resolution**: 30 km
- **Temporal Resolution**: Monthly and Annual

---

## Download WaPOR v3 RET Data

```python
import os
import numpy as np
import rasterio
from osgeo import gdal
import geopandas as gpd
from shapely.geometry import box


first_year = 2018
last_year = 2024

Level="L1" # L1 or L2
temporal_resolution="Annual" # Annual OR Monthly 
output_folder_path = "/Users/amanchaudhary/Documents/Resources/World_Bank/Zambia"   
geojson_boundary = "/Users/amanchaudhary/Documents/Resources/World_Bank/Zambia/Shapefile/Zambia_L0.geojson" 

output_folder = os.path.join(output_folder_path, f"WaPOR_v3_{Level}_RET_{temporal_resolution}") 



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
if Level == "L2":
    status, aoi_bounds, dataset_extent = check_extent(geojson_boundary, L2_extent)
    print(f"L2 Extent check: {status}")
    print(f"AOI bounds: {aoi_bounds}")
    print(f"Dataset extent: {dataset_extent}")

    
os.makedirs(output_folder, exist_ok=True)



filenames = []
if temporal_resolution == "Annual":
    for year in range(first_year, last_year + 1):

        url = f"https://gismgr.fao.org/DATA/WAPOR-3/MAPSET/{Level}-RET-A/WAPOR-3.{Level}-RET-A.{year}.tif"
        output_filename = f"RET_{year}0101.tif"
        filenames.append((url, output_filename))


elif temporal_resolution == "Monthly":
    for year in range(first_year, last_year + 1):
        for month in range(1, 13):
            url = f"https://gismgr.fao.org/DATA/WAPOR-3/MAPSET/{Level}-RET-M/WAPOR-3.{Level}-RET-M.{year}-{month:02d}.tif"
            output_filename = f"RET_{year}{month:02d}01.tif"
            filenames.append((url, output_filename))

else:
    raise ValueError("temporal_resolution must be 'Annual' or 'Monthly'")
    
total = len(filenames)
print("Total files:",total)


for url, output_filename in filenames:

    output_path = os.path.join(output_folder, output_filename)
    vsicurl_url = f"/vsicurl/{url}"
    temp_full = os.path.join(output_folder, f"temp_full_{output_filename}")
    temp_clip = os.path.join(output_folder, f"temp_clip_{output_filename}")

    

    # Skip if already processed
    if os.path.exists(output_path):
        print(f"✅ {output_filename} already exists, skipping...")
        continue

    print(f"📥 Downloading and processing {output_filename}")

    try:
        # Save full raster locally first
        gdal.Translate(
            destName=temp_full, 
            xRes=0.003,  # 300m resolution
            yRes=0.003,
            resampleAlg="near",
            srcDS=vsicurl_url)
    except Exception as e:
        print(f"❌ Failed to download full raster: {e}")
        continue


    try:
        # 2. Resample and clip the downloaded raster
        warp_options = gdal.WarpOptions(
            cutlineDSName=geojson_boundary,
            cropToCutline=True,
            dstNodata=-9999,
            
        )
        gdal.Warp(destNameOrDestDS=temp_clip, srcDSOrSrcDSTab=temp_full, options=warp_options)
    except Exception as e:
        print(f"❌ GDAL warp failed for {output_filename}: {e}")
        if os.path.exists(temp_full):
            os.remove(temp_full)
        continue

    # Scale and write output with compression
    try:
        with rasterio.open(temp_clip) as src:
            profile = src.profile
            data = src.read(1)
            nodata = src.nodata

            data = np.where(data == nodata, -9999, data)
            scaled_data = np.where(data != -9999, data * 0.1, -9999)

            profile.update(
                dtype=rasterio.float32,
                nodata=-9999,
                compress="LZW"
            )

            with rasterio.open(output_path, "w", **profile) as dst:
                dst.write(scaled_data.astype(rasterio.float32), 1)

        os.remove(temp_full)
        os.remove(temp_clip)
        print(f"✅ Processed and saved: {output_filename}")
    except Exception as e:
        print(f"❌ Failed to process/write {output_filename}: {e}")
        if os.path.exists(temp_full):
            os.remove(temp_full)
        if os.path.exists(temp_clip):
            os.remove(temp_clip)

```


