# Reference Evapotranspiration (RET) 
Reference evapotranspiration (RET) is defined as the evapotranspiration from a hypothetical reference crop. It simulates the behaviour of a well-watered grass surface and can be used to estimate potential ET for different crops by applying predefined crop coefficients. This information can be used in the design of irrigation schemes. Together with estimates of the evaporation, transpiration and interception, crop coefficients may be derived as the ratio between ETIa and RET. This information may be combined with land cover maps, to infer crop coefficients during the growing season for different type of crops. RET is not influenced by land cover and can be calculated using standard weather measurements and solar radiation.

For further information on the methodology read the WaPOR documentation available at: https://bitbucket.org/cioapps/wapor-et-look/wiki/Home

---


## Dataset Overview

- **Product**: WaPOR L1 v3
- **Source**: [https://console.cloud.google.com/storage/browser/fao-gismgr-wapor-3-data/DATA/WAPOR-3/MAPSET](https://console.cloud.google.com/storage/browser/fao-gismgr-wapor-3-data/DATA/WAPOR-3/MAPSET)
- **Format**: GeoTIFF
- **Extent**: Global
- **Data Availability**: 2018 - present 
- **Spatial Resolution**: 30 km
- **Temporal Resolution**: Monthly

---

## Download Monthly WaPOR L1 v3 RET Data

```python
import os
import numpy as np
import rasterio
from osgeo import gdal

firstyear = 2018
lastyear = 2024
  


output_folder = "/Users/amanchaudhary/Documents/Resources/World_Bank/Zambia/WaPOR_v3_RET_M"   
geojson_boundary = "/Users/amanchaudhary/Documents/Resources/World_Bank/Zambia/Shapefile/Zambia_L0.geojson" 



os.makedirs(output_folder, exist_ok=True)

for year in range(firstyear, lastyear + 1):
    for month in range(1, 13):

        filename = f"WAPOR-3.L1-RET-M.{year}-{month:02d}.tif"
        output_filename = f"WAPOR-3-L1-RET-M-{year}_{month:02d}.tif"
        output_path = os.path.join(output_folder, output_filename)
        

        # Skip if already processed
        if os.path.exists(output_path):
            print(f"✅ {filename} already exists, skipping...")
            continue

        print(f"📥 Downloading and processing {filename}")
        # Remote file URL via /vsicurl/
        url = f"https://gismgr.fao.org/DATA/WAPOR-3/MAPSET/L1-RET-M/{filename}"
        vsicurl_url = f"/vsicurl/{url}"
        temp_full = os.path.join(output_folder, f"temp_full_{filename}")
        temp_clip = os.path.join(output_folder, f"temp_clip_{filename}")



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
            print(f"❌ GDAL warp failed for {filename}: {e}")
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
            print(f"✅ Processed and saved: {filename}")
        except Exception as e:
            print(f"❌ Failed to process/write {filename}: {e}")
            if os.path.exists(temp_full):
                os.remove(temp_full)
            if os.path.exists(temp_clip):
                os.remove(temp_clip)


```




---

## Download Annual WaPOR L1 v3 RET Data

```python
import os
import numpy as np
import rasterio
from osgeo import gdal

firstyear = 2018
lastyear = 2024
  
output_folder = "/Users/amanchaudhary/Documents/Resources/World_Bank/Zambia/WaPOR_v3_RET_A"   
geojson_boundary = "/Users/amanchaudhary/Documents/Resources/World_Bank/Zambia/Shapefile/Zambia_L0.geojson" 


os.makedirs(output_folder, exist_ok=True)

for year in range(firstyear, lastyear + 1):

    filename = f"WAPOR-3.L1-RET-A.{year}.tif"
    output_filename = f"WAPOR-3-L1-RET-A-{year}.tif"
    output_path = os.path.join(output_folder, output_filename)
    

    # Skip if already processed
    if os.path.exists(output_path):
        print(f"✅ {filename} already exists, skipping...")
        continue

    print(f"📥 Downloading and processing {filename}")
    # Remote file URL via /vsicurl/
    url = f"https://gismgr.fao.org/DATA/WAPOR-3/MAPSET/L1-RET-A/{filename}"
    vsicurl_url = f"/vsicurl/{url}"
    temp_full = os.path.join(output_folder, f"temp_full_{filename}")
    temp_clip = os.path.join(output_folder, f"temp_clip_{filename}")



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
        print(f"❌ GDAL warp failed for {filename}: {e}")
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
        print(f"✅ Processed and saved: {filename}")
    except Exception as e:
        print(f"❌ Failed to process/write {filename}: {e}")
        if os.path.exists(temp_full):
            os.remove(temp_full)
        if os.path.exists(temp_clip):
            os.remove(temp_clip)


```
