import os
import re
import requests
import rasterio
from bs4 import BeautifulSoup
import numpy as np
from osgeo import gdal
import calendar
from datetime import datetime
import time
# Data Available 1999-2020

first_year = 2018
last_year = 2019

version='dmp_300m_v1_10daily' # dmp_300m_v1_10daily 0r  dmp_300m_v1_10daily
# Available:
# dmp_1km_v2_10daily = 1999-2020
# dmp_300m_v1_10daily = 2014-present


output_folder_path = "/Users/amanchaudhary/Documents/Resources/World_Bank/Jordan/dmp_10daily"
geojson_boundary = "/Users/amanchaudhary/Documents/Resources/World_Bank/Jordan/Shapefile/Jordan_L0.geojson"

output_folder = os.path.join(output_folder_path, f"{version}")

os.makedirs(output_folder, exist_ok=True)


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

for year in range(first_year, last_year + 1):
    if version=="dmp_1km_v2_10daily":
        year_url = f"https://globalland.vito.be/download/geotiff/dry_matter_productivity/dmp_1km_v2_10daily/{year}/"
    elif version=='dmp_300m_v1_10daily':
        year_url = f"https://globalland.vito.be/download/geotiff/dry_matter_productivity/dmp_300m_v1_10daily/{year}/"
    else:
        raise ValueError("temporal_resolution must be 'dmp_1km_v2_10daily' or 'dmp_300m_v1_10daily'")



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
                print("days_in_dekad",days_in_dekad)


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
            time.sleep(20)

        else:
            print(f"⚠️ No DMP-RTx file found in {folder_url}")


# ============================================================
# Aggregate Dekadal GeoTIFFs to Monthly
# ============================================================

import os
import re
import rasterio
import numpy as np
from collections import defaultdict
from datetime import datetime

# ==== Paths ====
input_folder = "dmp_1km_v2_10daily" # folder having dekadal raster files
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


# ============================================================
# Aggregate Monthly GeoTIFFs to Annual
# ============================================================

import os
import re
import rasterio
import numpy as np
from collections import defaultdict
from datetime import datetime

# ==== Paths ====
input_folder = "dmp_1km_v2_monthly"   # folder having monthly raster files
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
