# Total Biomass Production (TBP)
Total Biomass Production (TBP) is defined as the sum of the above-ground dry matter produced for a given year. TBP is calculated from Net Primary Production (NPP). TBP is expressed in kgDM/ha/day, and has thus different biomass units compared to NPP, with 1 gC/m2/day (NPP) = 22.222 kgDM/ha/day (DMP).

For further information on the methodology read the WaPOR documentation available at: [https://bitbucket.org/cioapps/wapor-et-look/wiki/Home](https://bitbucket.org/cioapps/wapor-et-look/wiki/Home)

---

## Dataset Overview

- **Product**: WaPOR L1 v3
- **Source**: [https://console.cloud.google.com/storage/browser/fao-gismgr-wapor-3-data/DATA/WAPOR-3/MAPSET](https://console.cloud.google.com/storage/browser/fao-gismgr-wapor-3-data/DATA/WAPOR-3/MAPSET)
- **Format**: GeoTIFF
- **Extent**: Global
- **Data Availability**: 2018 –present 
- **Spatial Resolution**: 300m
- **Temporal Resolution**: Monthly and Annual


---


## Download Monthly WaPOR L1 v3 TBP Data

```python

import os
import numpy as np
import rasterio
from osgeo import gdal



firstyear = 2024
lastyear = 2024


output_folder = "WaPOR_v3_L1_TBP_M"   
geojson_boundary = "Zambia_L0.geojson" 




os.makedirs(output_folder, exist_ok=True)

for year in range(firstyear, lastyear + 1):
    for month in range(1, 13):
        filename = f"WAPOR-3.L1-NPP-M.{year}-{month:02d}.tif"
        output_filename = f"wapor3_tbp_m_{year}_{month:02d}.tif"
        output_path = os.path.join(output_folder, output_filename)

        # Skip if already processed
        if os.path.exists(output_path):
            print(f"✅ {output_filename} already exists, skipping...")
            continue

        # Remote file URL via /vsicurl/
        url = f"https://gismgr.fao.org/DATA/WAPOR-3/MAPSET/L1-NPP-M/{filename}"
        vsicurl_url = f"/vsicurl/{url}"
        temp_clip = os.path.join(output_folder, f"temp_{output_filename}")

        print(f"Downloading...{filename}")

        try:
            warp_options = gdal.WarpOptions(
                cutlineDSName=geojson_boundary,
                cropToCutline=True,
                dstNodata=-9999
            )
            gdal.Warp(destNameOrDestDS=temp_clip, srcDSOrSrcDSTab=vsicurl_url, options=warp_options)
        except Exception as e:
            print(f"❌ GDAL warp failed for {filename}: {e}")
            continue

        # Scale and write output with compression
        try:
            with rasterio.open(temp_clip) as src:
                profile = src.profile
                data = src.read(1)
                nodata = src.nodata

                data = np.where(data == nodata, -9999, data)
                scaled_data = np.where(data != -9999, data * 0.001 * 22.222, -9999)

                profile.update(
                    dtype=rasterio.float32,
                    nodata=-9999,
                    compress="LZW"
                )

                with rasterio.open(output_path, "w", **profile) as dst:
                    dst.write(scaled_data.astype(rasterio.float32), 1)

            os.remove(temp_clip)
            print(f"✅ Processed and saved: {output_filename}")
        except Exception as e:
            print(f"❌ Failed to scale/write {filename}: {e}")
            if os.path.exists(temp_clip):
                os.remove(temp_clip)


```

---


## Download Annual WaPOR L1 v3 TBP Data

```python

import os
import numpy as np
import rasterio
from osgeo import gdal

firstyear = 2018
lastyear = 2024
  
output_folder = "WaPOR_v3_L1_TBP_A"   
geojson_boundary = "Zambia_L0.geojson" 



os.makedirs(output_folder, exist_ok=True)

for year in range(firstyear, lastyear + 1):

    filename = f"WAPOR-3.L1-TBP-A.{year}.tif"
    output_filename = f"WAPOR-3-L1-TBP-A-{year}.tif"
    output_path = os.path.join(output_folder, output_filename)

    # Skip if already processed
    if os.path.exists(output_path):
        print(f"✅ {output_filename} already exists, skipping...")
        continue

    # Remote file URL via /vsicurl/
    url = f"https://gismgr.fao.org/DATA/WAPOR-3/MAPSET/L1-TBP-A/{filename}"
    vsicurl_url = f"/vsicurl/{url}"


    print(f"Downloading...{filename}")

    try:
        warp_options = gdal.WarpOptions(
            cutlineDSName=geojson_boundary,
            cropToCutline=True,
            dstNodata=-9999
        )
        gdal.Warp(destNameOrDestDS=output_path, srcDSOrSrcDSTab=vsicurl_url, options=warp_options)
    except Exception as e:
        print(f"❌ GDAL warp failed for {filename}: {e}")
        continue




```