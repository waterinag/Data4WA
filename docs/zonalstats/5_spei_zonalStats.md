# Zonal Statistics for SPEI NetCDF

This script computes the mean SPEI (Standardized Precipitation-Evapotranspiration Index)
values for each administrative unit (districts/provinces) at every time step 
from a NetCDF dataset.
---


```python

import xarray as xr
import geopandas as gpd
import pandas as pd
import numpy as np
import os
import warnings

# Suppress specific PerformanceWarnings from geopandas
warnings.filterwarnings('ignore', category=pd.errors.PerformanceWarning)


raster_files_folder="/Users/amanchaudhary/Documents/Resources/World_Bank/SPEI_data"
geojson_boundary = "/Users/amanchaudhary/Documents/Resources/World_Bank/Zambia/Shapefile/Zambia_L2.geojson" 
output_folder = "/Users/amanchaudhary/Documents/Resources/World_Bank/SPEI_data"
os.makedirs(output_folder, exist_ok=True)

for filename in os.listdir(raster_files_folder):
    if filename.endswith('.nc'):
        print(filename)
        raster_file = os.path.join(raster_files_folder, filename)

        try:
            data = xr.open_dataset(raster_file)
        except ValueError as e:
            print(f"Error opening the NetCDF file: {e}")
            print("Make sure you have the necessary dependencies installed: netcdf4 or h5netcdf.")
            exit(1)

        zones_features = gpd.read_file(geojson_boundary)



        # Ensure the shapefile is in WGS 84 if not already
        if zones_features.crs.to_string() != 'epsg:4326':
            zones_features = zones_features.to_crs(epsg=4326)

        # Initialize an empty DataFrame to store results
        results_gdf = zones_features.copy()


        # Iterate over all time points in the dataset
        for time_point in data.time:
            target_time = pd.Timestamp(time_point.values)
            
            # Select the data for the specific time slice
            time_slice = data.sel(time=target_time)

            # Initialize a list to store mean SPEI values for this time slice
            means = []
            count = 1

            for _, polygon in zones_features.iterrows():
                # Get the bounds of the polygon
                minx, miny, maxx, maxy = polygon.geometry.bounds
                print("minx",minx)
                print("miny",miny)
                print("maxx",maxx)
                print("maxy",maxy)
                print(count)
                print("----------")
                count=count+1

            
                
                # Select the data within the bounds of the polygon
                subset = time_slice.sel(lat=slice(miny, maxy), lon=slice(minx, maxx))

                # If no data is found, add buffer size
                if subset['spei'].size == 0:
                    buffer = 0.15  # set buffer size
                    minx, miny, maxx, maxy = polygon.geometry.bounds
                    minx, miny, maxx, maxy = minx - buffer, miny - buffer, maxx + buffer, maxy + buffer
                    subset = time_slice.sel(lat=slice(miny, maxy), lon=slice(minx, maxx))

                    if subset['spei'].size == 0:
                        buffer = 0.25
                        minx, miny, maxx, maxy = polygon.geometry.bounds
                        minx, miny, maxx, maxy = minx - buffer, miny - buffer, maxx + buffer, maxy + buffer
                        subset = time_slice.sel(lat=slice(miny, maxy), lon=slice(minx, maxx))

                
                # Calculate the mean SPEI value for the subset
                if subset['spei'].size > 0:
                    mean_spei = subset['spei'].mean().values.item()  # Convert to a native Python scalar
                else:
                    mean_spei = np.nan  # Use NaN for missing values
                
                means.append(mean_spei)

            # Add the results to the GeoDataFrame with the column named after the time point
            results_gdf[target_time.strftime('%Y-%m')] = means

        # Save the GeoDataFrame to an Excel file
        results_gdf = results_gdf.drop(columns="geometry")


        base_name = os.path.splitext(filename)[0]
        output_csv = os.path.join(output_folder, f"{base_name}_zonal.csv")


        results_gdf.to_csv(output_csv, index=False)
        print(f"✅ Saved zonal results to {output_csv}")



```

