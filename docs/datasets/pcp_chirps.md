# Precipitation (CHIRPS)


## CHIRPS v3.0 Overview
CHIRPS v3.0 is available for three domains: Global, Africa, and Latin America. Similar to CHIRPS v2.0, two products of CHIRPS v3.0 are available. A preliminary version and a final version. The preliminary version is produced at the end of every pentad with rapidly available Global Telecommunication System (GTS) data, while the final version – produced about two weeks after the end of the month – incorporates data from the Global Historical Climatology Network (GHCN), and the Global Summary of the Day (GSOD).

CHIRPS v3.0 benefits from nearly four times more sources of gauge data compared to CHIRPS v2.0. This increased volume of observations significantly improves the spatial and temporal accuracy of rainfall estimates.


---
## Dataset Overview

- **Product**: CHIRPS v3
- **Source**: [https://data.chc.ucsb.edu/products/CHIRPS/v3.0/](https://data.chc.ucsb.edu/products/CHIRPS/v3.0/)
- **Format**: GeoTIFF
- **Extent**: Global
- **Data Availability**: 1981 - present
- **Spatial Resolution**: 5km
- **Temporal Resolution**:  Annual, Monthly , Dekadal and Daily

---



---

## Download CHIRPS PCP

The following script downloads **monthly CHIRPS v3.0 GeoTIFFs** for a given year range:

```python
import requests
import os
import numpy as np
import rasterio
from osgeo import gdal
import calendar

first_year = 1981
last_year = 2024


temporal_resolution="Annual" # Annual, Monthly , Dekadal or Daily
# Data Available : 1981 - present


output_folder_path = "/Users/amanchaudhary/Documents/Resources/World_Bank/Zambia"   
geojson_boundary = "/Users/amanchaudhary/Documents/Resources/World_Bank/Zambia/Shapefile/Zambia_L0.geojson" 

# ressampling 5km chirps pcp to 300m
resampling=False
# resampling=True


output_folder = os.path.join(output_folder_path, f"CHIRPS_v3_PCP_{temporal_resolution}") 

os.makedirs(output_folder, exist_ok=True)



filenames = []
if temporal_resolution == "Annual":
    for year in range(first_year, last_year + 1):
        url = f"https://data.chc.ucsb.edu/products/CHIRPS/v3.0/annual/global/tifs/chirps-v3.0.{year}.tif"
        output_filename = f"PCP_{year}0101.tif"
        filenames.append((url, output_filename))

elif temporal_resolution == "Monthly":
    for year in range(first_year, last_year + 1):
        for month in range(1, 13):
            url = f"https://data.chc.ucsb.edu/products/CHIRPS/v3.0/monthly/global/tifs/chirps-v3.0.{year}.{month:02d}.tif"
            output_filename = f"PCP_{year}{month:02d}01.tif"
            filenames.append((url, output_filename))
elif temporal_resolution == "Dekadal":
    for year in range(first_year, last_year + 1):
        for month in range(1, 13):
            for dekad in range(1, 4):  
                url = f"https://data.chc.ucsb.edu/products/CHIRPS/v3.0/dekads/global/tifs/chirps-v3.0.{year}.{month:02d}.{dekad}.tif"
                output_filename = f"PCP_{year}{month:02d}_D{dekad}.tif"
                filenames.append((url, output_filename))
elif temporal_resolution == "Daily":
    for year in range(first_year, last_year + 1):
        for month in range(1, 13):
            num_days = calendar.monthrange(year, month)[1]
            for day in range(1, num_days + 1):
                url = f"https://data.chc.ucsb.edu/products/CHIRPS/v3.0/daily/global/tifs/chirps-v3.0.{year}.{month:02d}.{day:02d}.tif"
                output_filename = f"PCP_{year}{month:02d}{day:02d}.tif"
                filenames.append((url, output_filename))


else:
    raise ValueError("temporal_resolution must be 'Annual' or 'Monthly'")
    
total = len(filenames)
print("Total files:",total)


for url, output_filename in filenames:

    output_path = os.path.join(output_folder, output_filename)

    print(f"Downloading {output_filename} from {url} ...")

    vsicurl_url = f"/vsicurl/{url}"

    if resampling:

        try:
            temp_full = os.path.join(output_folder, f"temp_full_{output_filename}")

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
            gdal.Warp(destNameOrDestDS=output_path, srcDSOrSrcDSTab=temp_full, options=warp_options)
        except Exception as e:
            print(f"❌ GDAL warp failed for {output_filename}: {e}")

        # Remove intermediate file
        if os.path.exists(temp_full):
            os.remove(temp_full)
        print(f"✅ Processed and saved: {output_filename}")


    else:
        warp_options = gdal.WarpOptions(
            cutlineDSName=geojson_boundary,
            cropToCutline=True,
            dstNodata=-9999
        )
        gdal.Warp(destNameOrDestDS=output_path, srcDSOrSrcDSTab=vsicurl_url, options=warp_options)
        print(f"✅ Processed and saved: {output_filename}")
        


```
