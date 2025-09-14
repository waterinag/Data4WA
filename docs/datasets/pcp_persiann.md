# Precipitation (PERSIANN)


## PERSIANN Overview
PERSIANN-CDR is a daily quasi-global precipitation product that spans the period from 1983-01-01 to present. The data is produced quarterly, with a typical lag of three months. The product is developed by the Center for Hydrometeorology and Remote Sensing at the University of California, Irvine (UC-IRVINE/CHRS) using Gridded Satellite (GridSat-B1) IR data that are derived from merging ISCCP B1 IR data, along with GPCP version 2.2.

---
## Dataset Overview

- **Product**: PERSIANN
- **Source**: [https://developers.google.com/earth-engine/datasets/catalog/NOAA_PERSIANN-CDR#bands](https://developers.google.com/earth-engine/datasets/catalog/NOAA_PERSIANN-CDR#bands)
- **Format**: GeoTIFF
- **Extent**: Global
- **Data Availability**: 1983-present
- **Spatial Resolution**: 27km
- **Temporal Resolution**: Daily 

---



---

## Download Monthly PERSIANN PCP

The following script downloads **monthly PERSIANN PCP GeoTIFFs (in mm/day)** for a given year range from Google Earth Engine:

```python
import ee
import geemap
import os
import json


# Trigger the authentication flow.
ee.Authenticate()

# Initialize the library.
ee.Initialize(project='waterinfor') # <-- change to your GEE project


# Define the start and end years.
firstyear = 2023
lastyear = 2024

# Create output directories if they do not exist.
output_dir = 'PCP_persiann_Monthly'

if not os.path.exists(output_dir):
    os.makedirs(output_dir)


years = ee.List.sequence(firstyear, lastyear)

filenames =[]

for year in range(firstyear, lastyear + 1):
    for month in range(1,13):
        filename = f"pcp_persiann_{year}_{month:02d}"
        filenames.append(filename)

print(f"🗂️ Total names process: {len(filenames)}")

# Filter the collection by date and select the 'precipitation' band.
precipdata = ee.ImageCollection("NOAA/PERSIANN-CDR") \
    .filter(ee.Filter.date(f'{firstyear}-01-01', f'{lastyear}-12-31')) \
    .select('precipitation')

# Function to add Month and Year properties based on each image’s system:time_start.
def set_date_properties(img):
    date = ee.Date(img.get('system:time_start'))
    # Use the standard properties 'month' and 'year'
    return img.set({
        'Month': date.get('month'),
        'Year': date.get('year')
    })

pcpts_daily = precipdata.map(set_date_properties)

# --- Generate Monthly Precipitation Totals ---
def monthly_image(year):
    def process_month(m):
        # Sum all daily images for a given year and month.
        monthly_sum = pcpts_daily.filter(ee.Filter.eq('Year', year)) \
                                 .filter(ee.Filter.eq('Month', m)) \
                                 .sum()
        date = ee.Date.fromYMD(year, m, 1)
        return monthly_sum.set({
            'Year': year,
            'Month': m,
            'date': date,
            'system:time_start': date.millis()
        }).rename('PCP')
    # Create a list of monthly images for months 1 through 12.
    return ee.ImageCollection(ee.List.sequence(1, 12).map(process_month))

# Map over all years and flatten the results into one ImageCollection.
monthly_list = ee.List(years.map(lambda y: monthly_image(ee.Number(y)).toList(12))).flatten()

# print(monthly_list)
persiann_PCP_M = ee.ImageCollection(monthly_list)

count = persiann_PCP_M.size().getInfo()
print(f"📅 Total images: {count}")

# print("persiann_PCP_M", persiann_PCP_M)


# def annual_image(year):
#     # Sum monthly images for a given year.
#     annual_sum = persiann_PCP_M.filter(ee.Filter.eq('Year', year)) \
#                                .select('PCP').sum()
#     date = ee.Date.fromYMD(year, 1, 1)
#     return annual_sum.set({
#         'year': year,
#         'date': date,
#         'system:time_start': date.millis()
#     })

# annual_list = years.map(annual_image)
# persiann_PCP_A = ee.ImageCollection(annual_list)

# print("persiann_PCP_A", persiann_PCP_A.getInfo())




# Here we use a global bounding box; adjust as needed.
roi = ee.Geometry.BBox(-180, -80, 180, 80)





# Export monthly images.
geemap.ee_export_image_collection(
    persiann_PCP_M,
    out_dir=output_dir,
    scale=27000,       # Adjust resolution (in meters) as needed.
    crs='EPSG:4326',
    region=roi,
    filenames=filenames
)



print("Export complete!")
            


```


