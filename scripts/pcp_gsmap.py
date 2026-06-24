import ee
import geemap
import os
import json
from datetime import date, timedelta

# Trigger the authentication flow.
ee.Authenticate()

# Initialize the library.
ee.Initialize(project='waterinfor') # <-- change to your GEE project

# Define the start and end years.
firstyear = 2024
lastyear = 2024

output_directory = 'GsMap_Daily'  # Change to your desired folder path.


years = ee.List.sequence(firstyear, lastyear)

start_date = date(firstyear, 1, 1)
end_date = date(lastyear, 12, 31)
filenames = []
dates = []

current_date = start_date
while current_date <= end_date:
    fname = f"pcp_gsmap_{current_date.year}_{current_date.month:02d}_{current_date.day:02d}"
    filenames.append(fname)
    dates.append(current_date.strftime("%Y-%m-%d"))
    current_date += timedelta(days=1)

print(f"🗂️ Total days to process: {len(filenames)}")

hourly_ic = ee.ImageCollection("JAXA/GPM_L3/GSMaP/v8/operational") \
    .filterDate(f'{firstyear}-01-01', f'{lastyear}-12-31') \
    .select('hourlyPrecipRateGC')


# Function to compute daily total
def make_daily_image(date_str):
    start = ee.Date(date_str)
    end = start.advance(1, 'day')

    daily_sum = hourly_ic.filterDate(start, end).sum() \
        .rename('PCP') \
        .set({
            'system:time_start': start.millis(),
            'date': start.format('YYYY_MM_dd')
        })

    return daily_sum

daily_images = ee.ImageCollection(ee.List([make_daily_image(d) for d in dates]))


count = daily_images.size().getInfo()
print(f"📅 Total daily images: {count}")


geom = ee.Geometry.BBox(-180, -80, 180, 80)


feature = ee.Feature(geom, {})
roi = feature.geometry()



# Export all images to Google Drive
geemap.ee_export_image_collection(
    daily_images,
    out_dir=output_directory,
    region=roi,
    scale=15000,             # You can use 10000 or 15000
    crs='EPSG:4326',
    filenames=filenames

)

print("🚀 Export tasks created. Check Earth Engine Tasks tab or Code Editor.")


# ============================================================
# Aggregate Daily GeoTIFFs to Monthly
# ============================================================

import os
import numpy as np
import rasterio
from datetime import datetime

# ==== Paths ====
input_folder = "/Volumes/ExternalHDD/RS_Data/GsMap_Daily"
output_folder = "/Volumes/ExternalHDD/RS_Data/GsMap_Monthly"

firstyear = 2024
lastyear = 2024  # inclusive

# Create the output folder if it doesn't exist
os.makedirs(output_folder, exist_ok=True)

# Loop through years
for year in range(firstyear, lastyear + 1):
    for month in range(1, 13):
        sum_array = None
        profile = None

        # Loop through all possible days in month
        for day in range(1, 32):  # max days in a month
            try:
                # Validate date (skip invalid ones like Feb 30)
                date_obj = datetime(year, month, day)
            except ValueError:
                continue

            # File naming pattern — adjust if yours differs
            daily_filename = f"pcp_gsmap_{year}_{month:02d}_{day:02d}.tif"
            input_path = os.path.join(input_folder, daily_filename)

            if not os.path.exists(input_path):
                print(f"File {input_path} does not exist, skipping day {day}.")
                continue

            with rasterio.open(input_path) as src:
                data = src.read(1)

                if sum_array is None:
                    sum_array = np.zeros_like(data, dtype=np.float32)
                    profile = src.profile

                sum_array += data.astype(np.float32)

        # Save the monthly total
        if sum_array is not None:
            profile.update(dtype=rasterio.float32, count=1)
            output_path = os.path.join(output_folder, f"pcpm_gsmap_{year}_{month:02d}.tif")
            with rasterio.open(output_path, "w", **profile) as dst:
                dst.write(sum_array, 1)
            print(f"Monthly raster for {year}-{month:02d} saved to {output_path}")
        else:
            print(f"No daily rasters found for {year}-{month:02d}.")
