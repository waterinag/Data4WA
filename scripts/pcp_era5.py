import ee
import geemap
import os
import json

# Trigger the authentication flow.
ee.Authenticate()

# Initialize the library.
ee.Initialize(project='waterinfor') # <-- change to your GEE project


# Specify the output directory where the images will be saved.
output_directory = 'pcp_era5_M'  # Change to your desired folder path.


# Define the start and end years.
firstyear = 2024
lastyear = 2024
years = ee.List.sequence(firstyear, lastyear)



filenames =[]

for year in range(firstyear, lastyear + 1):
    for month in range(1,13):
        filename = f"pcp_era5_{year}_{month:02d}"
        filenames.append(filename)



# Load the monthly ERA5 Land dataset and filter by date.
precipdata_M = ee.ImageCollection("ECMWF/ERA5_LAND/MONTHLY_AGGR") \
    .filter(ee.Filter.date(f'{firstyear}-01-01', f'{lastyear}-12-31')) \
    .select('total_precipitation_sum')

# Function to convert units from meters to millimeters and set metadata.
def convert_to_mm(img):
    date = ee.Date(img.get('system:time_start'))
    year = date.get('year')
    month = date.get('month')
    new_date = ee.Date.fromYMD(year, month, 1)
    return img.multiply(ee.Image(1000)) \
              .set('Year', year) \
              .set('Month', month) \
              .set('date', new_date) \
              .rename('PCP') \
              .set('system:time_start', new_date.millis())

# Map the conversion function over the collection.
era5_PCP_M = precipdata_M.map(convert_to_mm)


# Define an export region.
# Here, a global rectangle is used. Change this to a smaller region if needed.
geom = ee.Geometry.BBox(-180, -80, 180, 80)


feature = ee.Feature(geom, {})
roi = feature.geometry()


# Export the monthly images as GeoTIFFs.
geemap.ee_export_image_collection(
    era5_PCP_M,
    out_dir=output_directory,
    scale=15000,          # Adjust the scale (in meters) as required.
    crs='EPSG:4326',      # The coordinate reference system.
    region=roi,
    filenames=filenames
)

print("Export complete!")
