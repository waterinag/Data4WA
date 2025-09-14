# Zonal Statistics for Raster Time Series

This script computes zonal statistics (mean values) of a time-series of raster files 
(e.g., WaPOR AETI rasters) over vector polygon boundaries (e.g. districts, basins). 
The result is a CSV table with one row per polygon feature (e.g. districts, basins) and one column per raster file.
---


```python

import geopandas as gpd
import rasterio
from rasterstats import zonal_stats
import pandas as pd
import os


# Path to the folder containing raster files
raster_files_folder = '/Users/amanchaudhary/Documents/Resources/World_Bank/Zambia/WaPOR_ETb_A'
geojson_boundary = "/Users/amanchaudhary/Documents/Resources/World_Bank/Zambia/Shapefile/Zambia_L2.geojson" 
output_csv= "/Users/amanchaudhary/Documents/Resources/World_Bank/Zambia/ZonalStats/WaPOR_ETb_A.csv"   


# Load shapefile
zones_features = gpd.read_file(geojson_boundary)

# Dictionary to store zonal statistics for each month
stats_by_file = {}

# Iterate over raster files in the folder
for filename in os.listdir(raster_files_folder):
    if filename.endswith('.tif'):
        print(filename)
        
        raster_file = os.path.join(raster_files_folder, filename)
        with rasterio.open(raster_file) as src:
            affine = src.transform
            stats = zonal_stats(zones_features.geometry, src.read(1), affine=affine, stats=['mean'], nodata=src.nodata)
            stats_by_file[filename] = [
                round(stat["mean"], 2) if stat["mean"] is not None else None
                for stat in stats
            ]
            

# Build DataFrame with zonal stats
df_stats = pd.DataFrame(stats_by_file)

# Merge all attributes from the GeoJSON (except geometry)
zones_attr = zones_features.drop(columns="geometry")
df = pd.concat([zones_attr, df_stats], axis=1)

# Ensure clean order: attributes first, then raster columns sorted
attr_cols = [c for c in zones_attr.columns]  # all attributes (index + properties)
raster_cols = sorted(df_stats.columns)
df = df[attr_cols + raster_cols]

# Save CSV (no geometry included)
df.to_csv(output_csv, index=False)

```


