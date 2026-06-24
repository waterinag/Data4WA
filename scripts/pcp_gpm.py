import ee
import geemap
import os
import json

# Trigger the authentication flow.
ee.Authenticate()

# Initialize the library.
ee.Initialize(project='waterinfor') # <-- change to your GEE project


# Define the start and end years.
firstyear = 2022
lastyear = 2023


output_directory = 'PCP_GPM_Monthly'  # Change to your desired folder path.


years = ee.List.sequence(firstyear, lastyear)


filenames =[]

for year in range(firstyear, lastyear + 1):
    for month in range(1,13):
        filename = f"pcpm_gpm_{year}_{month:02d}"
        filenames.append(filename)


# ---------------------
# Here the unit mm/hour not mm
# ---------------------
precipdata = ee.ImageCollection("NASA/GPM_L3/IMERG_MONTHLY_V07") \
    .filterDate(f'{firstyear}-01-01', f'{lastyear}-12-31') \
    .select('precipitation')

# Function to add 'Month' and 'Year' properties to each image based on its time.
def add_month_year(img):
    date = ee.Date(img.get('system:time_start'))
    return img.set({
        'Month': date.get('month'),
        'Year': date.get('year')
    })


pcpts_monthly = precipdata.map(add_month_year)


# Build a monthly aggregated ImageCollection.
def monthly_image(year):
    def month_func(month):
        date = ee.Date.fromYMD(year, month, 1)
        days_in_month = date.advance(1, 'month').difference(date, 'day')

        # Get the single monthly image
        monthly_img = pcpts_monthly.filter(ee.Filter.eq('Year', year)) \
                                .filter(ee.Filter.eq('Month', month)) \
                                .first()

        # Convert mm/hr to mm/month
        mm_per_month = ee.Image(monthly_img) \
        .multiply(24).multiply(days_in_month) \
        .unmask(0) # fill nodata with 0


        return mm_per_month.set({
            'Year': year,
            'Month': month,
            'date': date,
            'system:time_start': date.millis()
        }).rename('PCP')

    # Create a list of monthly images (for months 1 through 12)
    monthly_list = ee.List.sequence(1, 12).map(month_func)
    return ee.ImageCollection(monthly_list)



# Create a flattened ImageCollection containing monthly aggregates for each year.
monthly_collections = years.map(lambda y: monthly_image(ee.Number(y)))


def merge_collections(list_of_collections):
    def merge_func(col, acc):
        return ee.ImageCollection(acc).merge(ee.ImageCollection(col))
    return ee.ImageCollection(ee.List(list_of_collections).iterate(merge_func, ee.ImageCollection([])))

GPM_PCP_M = merge_collections(monthly_collections)


# Define an export region.
# Here, a global rectangle is used. Change this to a smaller region if needed.
geom = ee.Geometry.BBox(-180, -80, 180, 80)


feature = ee.Feature(geom, {})
roi = feature.geometry()


# Export the monthly images as GeoTIFFs.
geemap.ee_export_image_collection(
    GPM_PCP_M,
    out_dir=output_directory,
    scale=15000,          # Adjust the scale (in meters) as required.
    crs='EPSG:4326',      # The coordinate reference system.
    region=roi,
    filenames=filenames
)

print("Export complete!")
