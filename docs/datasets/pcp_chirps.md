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
- **Data Availability**: 1981 - 
- **Spatial Resolution**: 5km
- **Temporal Resolution**: Monthly

---



---

## Download Monthly CHIRPS PCP

The following script downloads **monthly CHIRPS v3.0 GeoTIFFs** for a given year range:

```python
import requests
import os
import numpy as np
import rasterio
from osgeo import gdal


firstyear = 2018
lastyear = 2024


output_folder = "/Users/amanchaudhary/Documents/Resources/World_Bank/Zambia/CHIRPS_v3_PCP_M"   
geojson_boundary = "/Users/amanchaudhary/Documents/Resources/World_Bank/Zambia/Shapefile/Zambia_L0.geojson" 


# resampling 5km chirps pcp to 300m

resampling=False
# resampling=True

os.makedirs(output_folder, exist_ok=True)


for year in range(firstyear, lastyear + 1):
    for month in range(1,13):
        # Format filename as mYYYYmm.zip (e.g., m201202.zip)
        filename = f"chirps-v3.0.{year}.{month:02d}.tif"
        output_filename = f"chirpsv3_pcp_m_{year}_{month:02d}.tif"
        output_path = os.path.join(output_folder, output_filename)


        url = f"https://data.chc.ucsb.edu/products/CHIRPS/v3.0/monthly/global/tifs/{filename}"
        print(f"Downloading {filename} from {url} ...")

        vsicurl_url = f"/vsicurl/{url}"

        if resampling:

            try:
                temp_full = os.path.join(output_folder, f"temp_full_{filename}")

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
                print(f"❌ GDAL warp failed for {filename}: {e}")

            # Remove intermediate file
            if os.path.exists(temp_full):
                os.remove(temp_full)
            print(f"✅ Processed and saved: {filename}")


        else:
            warp_options = gdal.WarpOptions(
                cutlineDSName=geojson_boundary,
                cropToCutline=True,
                dstNodata=-9999
            )
            gdal.Warp(destNameOrDestDS=output_path, srcDSOrSrcDSTab=vsicurl_url, options=warp_options)
            print(f"✅ Processed and saved: {filename}")
            


```

---
## Download Annual CHIRPS PCP

The following script downloads **annual CHIRPS v3.0 GeoTIFFs** for a given year range:

```python
import requests
import os
import numpy as np
import rasterio
from osgeo import gdal


firstyear = 2018
lastyear = 2024

output_folder = "/Users/amanchaudhary/Documents/Resources/World_Bank/Zambia/CHIRPS_v3_PCP_A"   
geojson_boundary = "/Users/amanchaudhary/Documents/Resources/World_Bank/Zambia/Shapefile/Zambia_L0.geojson" 


# resampling 5km chirps pcp to 300m

resampling=False
# resampling=True



os.makedirs(output_folder, exist_ok=True)


for year in range(firstyear, lastyear + 1):

    filename = f"chirps-v3.0.{year}.tif"
    output_filename = f"chirpsv3_pcp_a_{year}.tif"
    output_path = os.path.join(output_folder, output_filename)


    

    url = f"https://data.chc.ucsb.edu/products/CHIRPS/v3.0/annual/global/tifs/{filename}"
    print(f"Downloading {filename} from {url} ...")

    vsicurl_url = f"/vsicurl/{url}"

    if resampling:

        try:
            temp_full = os.path.join(output_folder, f"temp_full_{filename}")

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
            print(f"❌ GDAL warp failed for {filename}: {e}")

        # Remove intermediate file
        if os.path.exists(temp_full):
            os.remove(temp_full)
        print(f"✅ Processed and saved: {filename}")


    else:
        warp_options = gdal.WarpOptions(
            cutlineDSName=geojson_boundary,
            cropToCutline=True,
            dstNodata=-9999
        )
        gdal.Warp(destNameOrDestDS=output_path, srcDSOrSrcDSTab=vsicurl_url, options=warp_options)
        print(f"✅ Processed and saved: {filename}")
        
          


```

---
