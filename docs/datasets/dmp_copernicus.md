# Dry Matter Productivity (DMP)

DMP Represents the overall growth rate or dry biomass increase of the vegetation and is directly related to ecosystem Net Primary Production (NPP), however with units customized for agro-statistical purposes (kg/ha/day). Every 10-days estimates are available at global scale in the spatial resolution of about 1km and with the temporal extent from 1999 to June 2020.

---


## Dataset Overview

- **Product**: Copernicus
- **Source**: [https://land.copernicus.eu/en/products/vegetation/dry-matter-productivity-v2-0-1km](https://land.copernicus.eu/en/products/vegetation/dry-matter-productivity-v2-0-1km)
- **Format**: GeoTIFF
- **Extent**: Global
- **Data Availability**: 1999-2020
- **Spatial Resolution**: 1 km
- **Temporal Resolution**: 10-daily

---

!!! warning "Important"  

    If you encounter errors like **"Too Many Requests"** or connection issues 
    while running the script, it usually means the **Copernicus server** is 
    throttling requests. Please wait for some time and try again later.

    - Data availability: 1999–2020 (for DMP v2 product).

    - **Scale factor**:
        - DMP values are stored as integers (Digital Numbers, DN).
        - Conversion to physical values (kg/ha/day) is done as:  
        `PV = DN × 0.01`
        - To represent dekadal productivity (kg/ha/dekad), multiply by **10**:  
        `PV = DN × 0.01 × 10`

        
    - The script outputs **clipped, scaled rasters in units of kg/ha/dekad**.


    📖 **Product User Manual**:  
    [Copernicus DMP v2 User Manual](https://land.copernicus.eu/en/technical-library/product-user-manual-dry-and-gross-dry-matter-productivity-version-2/@@download/file)



## Download Dekadal DMP Data

This script processes DMP (Dry Matter Productivity) data downloaded from the Copernicus Global Land Service (https://land.copernicus.eu/global/).

```python

import os
import re
import requests
import rasterio
from bs4 import BeautifulSoup
import numpy as np
from osgeo import gdal
import calendar
from datetime import datetime

# Data Available 1999-2020

start_year = 2018
end_year = 2018


output_folder = "dmp_1km_v2_10daily"
geojson_boundary = "Zambia_L0.geojson" 


scale_factor = 0.01


# scale_factor = 0.01 for DMP; use 0.02 if working with GDMP


def get_dekad_days(year, month, dekad_index):
    """
    Returns the number of days in a given dekad.
    dekad_index = 1, 2, or 3
    """
    if dekad_index == 1:
        return 10
    elif dekad_index == 2:
        return 10
    elif dekad_index == 3:
        return calendar.monthrange(year, month)[1] - 20  # remaining days
    else:
        raise ValueError("Dekad index must be 1, 2, or 3")
    

os.makedirs(output_folder, exist_ok=True)

rt_pattern = re.compile(r"DMP-RT(\d+)")

for year in range(start_year, end_year + 1):
    year_url = f"https://globalland.vito.be/download/geotiff/dry_matter_productivity/dmp_1km_v2_10daily/{year}/"


    print(f"\n📅 Year: {year}")
    print(f"🔍 Fetching index: {year_url}")
    try:
        response = requests.get(year_url)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"❌ Failed to fetch index for {year}: {e}")
        continue

    # Parse folder names like 20140110, 20140120...
    soup = BeautifulSoup(response.text, "html.parser")
    links = soup.find_all("a")
    folders = [link.get("href").strip("/") for link in links if link.get("href").startswith(str(year))]

    print(f"📁 Found {len(folders)} decadal folders")

    for folder in folders:
        folder_url = f"{year_url}{folder}/"
        try:
            sub_response = requests.get(folder_url)
            sub_response.raise_for_status()
        except requests.exceptions.RequestException as e:
            print(f"❌ Failed to fetch subfolder {folder}: {e}")
            continue

        sub_soup = BeautifulSoup(sub_response.text, "html.parser")
        file_links = [link.get("href") for link in sub_soup.find_all("a") if link.get("href").endswith(".tiff")]


        # Filter only DMP-RTx (exclude QFLAGs)
        rt_files = []
        for f in file_links:
            if "DMP-RT" in f and "QFLAG" not in f:
                match = rt_pattern.search(f)
                if match:
                    rt_num = int(match.group(1))
                    rt_files.append((rt_num, f))


        if rt_files:
            # Select file with highest RTx version
            selected_file = max(rt_files, key=lambda x: x[0])[1]
            file_url = f"{folder_url}{selected_file}"
            clipped_file = os.path.join(output_folder, f"clipped_{selected_file}")
            output_path = os.path.join(output_folder, selected_file)

            if os.path.exists(output_path):
                print(f"✅ Already exists: {selected_file}")
                continue

            print(f"⬇️  Downloading: {file_url}")

            vsicurl_url = f"/vsicurl/{file_url}"


            # Cliping for GeoJSON Boundary
            warp_options = gdal.WarpOptions(
                cutlineDSName=geojson_boundary,
                cropToCutline=True,
                dstNodata=-9999
                )
            gdal.Warp(destNameOrDestDS=clipped_file, srcDSOrSrcDSTab=vsicurl_url, options=warp_options)


            with rasterio.open(clipped_file) as src:
                arr = src.read(1).astype(np.float32)
                profile = src.profile.copy()

                # Replace invalid values with NaN
                arr[(arr >= 32767) | (arr < 0)] = np.nan

                date_obj = datetime.strptime(folder, "%Y%m%d")
                dekad_index = 1 if date_obj.day <= 10 else 2 if date_obj.day <= 20 else 3
                days_in_dekad = get_dekad_days(date_obj.year, date_obj.month, dekad_index)


                # Apply scale factor
                arr = arr * scale_factor * days_in_dekad

                # Convert NaN to -9999 nodata
                arr = np.where(np.isnan(arr), -9999, arr).astype(np.float32)

                # Update profile for new raster
                profile.update(dtype=rasterio.float32, nodata=-9999, compress="lzw")

                # Write NEW GeoTIFF
                with rasterio.open(output_path, "w", **profile) as dst:
                    dst.write(arr, 1)

            if os.path.exists(clipped_file):
                os.remove(clipped_file)

            # Preprocessing 
            print(f"✅ Saved: {output_path}")

        else:
            print(f"⚠️ No DMP-RTx file found in {folder_url}")



```



---


## Aggregate Dekadal GeoTIFFs to Monthly


```python
import os
import re
import rasterio
import numpy as np
from collections import defaultdict
from datetime import datetime

# ==== Paths ====
input_folder = "dmp_1km_v2_10daily"
output_folder = "dmp_1km_v2_monthly"
os.makedirs(output_folder, exist_ok=True)

# Regex to extract date from filenames
date_pattern = re.compile(r".*_(\d{8})\d{4}_.*\.tiff$")

# Group files by year-month
files_by_month = defaultdict(list)

for fname in os.listdir(input_folder):
    if fname.lower().endswith(".tiff" or '.tif'):
        match = date_pattern.match(fname)
        
        if match:
            date_str = match.group(1)  # YYYYMMDD
            date_obj = datetime.strptime(date_str, "%Y%m%d")
            year_month = date_obj.strftime("%Y-%m")
            files_by_month[year_month].append(os.path.join(input_folder, fname))
            


# Process each month
for ym, file_list in sorted(files_by_month.items()):
    sum_array = None
    count_array = None
    profile = None
    nodata = None

    for f in file_list:
        with rasterio.open(f) as src:
            data = src.read(1).astype(np.float32)
            nodata = src.nodata if src.nodata is not None else -9999

            # replace nodata with NaN
            data[data == nodata] = np.nan

            if sum_array is None:
                sum_array = np.full_like(data, np.nan, dtype=np.float32)
                count_array = np.zeros_like(data, dtype=np.int16)
                profile = src.profile
                profile.update(dtype=rasterio.float32, count=1, nodata=nodata)

            # add values where valid
            valid_mask = ~np.isnan(data)
            # accumulate sum
            sum_array[valid_mask] = np.where(
                np.isnan(sum_array[valid_mask]),
                data[valid_mask],
                sum_array[valid_mask] + data[valid_mask]
            )
            # count valid observations
            count_array[valid_mask] += 1

    monthly_data = sum_array


    if monthly_data is not None:
        year, month = ym.split("-")
        output_path = os.path.join(output_folder, f"dmp_{year}_{month}.tif")

        with rasterio.open(output_path, "w", **profile) as dst:
            output_data = np.where(np.isnan(monthly_data), nodata, monthly_data)
            dst.write(output_data.astype(np.float32), 1)

        print(f"Monthly raster saved: {output_path}")


print("All monthly rasters created successfully!")




```

---

## Aggregate Monthly GeoTIFFs to Annual


```python

import os
import re
import rasterio
import numpy as np
from collections import defaultdict
from datetime import datetime

# ==== Paths ====
input_folder = "dmp_1km_v2_monthly"   
output_folder = "dmp_1km_v2_annual"
os.makedirs(output_folder, exist_ok=True)

date_pattern = re.compile(r".*_(\d{4})_(\d{2})\.tif$")

# Group files by year
files_by_year = defaultdict(list)

for fname in os.listdir(input_folder):
    if fname.lower().endswith((".tif", ".tiff")):
        match = date_pattern.match(fname)
        if match:
            year = match.group(1)
            files_by_year[year].append(os.path.join(input_folder, fname))


# ==== Process each year ====
for year, file_list in sorted(files_by_year.items()):
    sum_array = None
    count_array = None
    profile = None
    nodata = None

    for f in file_list:
        with rasterio.open(f) as src:
            data = src.read(1).astype(np.float32)
            nodata = src.nodata if src.nodata is not None else -9999

            # replace nodata with NaN
            data[data == nodata] = np.nan

            if sum_array is None:
                sum_array = np.full_like(data, np.nan, dtype=np.float32)
                count_array = np.zeros_like(data, dtype=np.int16)
                profile = src.profile
                profile.update(dtype=rasterio.float32, count=1, nodata=nodata)

            # add values where valid
            valid_mask = ~np.isnan(data)
            sum_array[valid_mask] = np.where(
                np.isnan(sum_array[valid_mask]),
                data[valid_mask],
                sum_array[valid_mask] + data[valid_mask]
            )
            count_array[valid_mask] += 1

    annual_data = sum_array

    if annual_data is not None:
        output_path = os.path.join(output_folder, f"dmp_{year}.tif")

        with rasterio.open(output_path, "w", **profile) as dst:
            output_data = np.where(np.isnan(annual_data), nodata, annual_data)
            dst.write(output_data.astype(np.float32), 1)

        print(f"Annual raster saved: {output_path}")

print("All annual rasters created successfully!")




```
