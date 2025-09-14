# Pixel Count and Area Statistics for LULC Raster

This script calculates pixel counts and corresponding area (in m²) of each
land cover class within polygon boundaries (e.g., districts, basins etc).
It produces two CSV outputs:
1. Pixel counts per class per polygon.
2. Converted areas in square meters (or hectares, if adjusted).
---


```python

import geopandas as gpd
import rasterio
from rasterstats import zonal_stats
import pandas as pd
from osgeo import gdal
import os


geojson_boundary = "/Users/amanchaudhary/Documents/Resources/World_Bank/Zambia/Shapefile/Zambia_L2.geojson" 
lcc_raster = "/Users/amanchaudhary/Documents/Resources/World_Bank/Zambia/LULC/WaPOR_v2_LULC/WaPOR_v2_LULC_2022_reclass.tif"
output_base = "/Users/amanchaudhary/Documents/Resources/World_Bank/Zambia/LULC_Stats/WaPOR_v2_LULC_2022"


count_csv = output_base + "_pixelCount.csv"
area_csv = output_base + "_area_m2.csv"


zones_features = gpd.read_file(geojson_boundary)



with rasterio.open(lcc_raster) as src:
    raster_crs = src.crs
    data = src.read(1)
    affine = src.transform
    nodata = src.nodata


if not zones_features.crs:
    raise ValueError("Vector data has no CRS defined.")
if not raster_crs:
    raise ValueError("Raster data has no CRS defined.")
if zones_features.crs != raster_crs:
    raise ValueError(f"CRS mismatch:\nVector CRS: {zones_features.crs}\nRaster CRS: {raster_crs}")


stats = zonal_stats(
    vectors=zones_features["geometry"],
    raster=data,
    affine=affine,
    categorical=True,
    nodata=nodata
)



df_stats = pd.DataFrame(stats).fillna(0)


# Merge all attributes from the GeoJSON (except geometry)
zones_attr = zones_features.drop(columns="geometry")
df_count = pd.concat([zones_attr, df_stats], axis=1)

# Ensure clean order: attributes first, then raster columns sorted
attr_cols = [c for c in zones_attr.columns]  # all attributes (index + properties)
raster_cols = sorted(df_stats.columns)
df_count = df_count[attr_cols + raster_cols]

# Save CSV (no geometry included)
df_count.to_csv(count_csv, index=False)

print(f"✅ Pixel counts saved to {count_csv}")





reprojected_raster = "tem_reprojected_3857.tif"

gdal.Warp(
    destNameOrDestDS=reprojected_raster,
    srcDSOrSrcDSTab=lcc_raster,
    dstSRS="EPSG:3857",
    format="GTiff",
    xRes=None,  # auto
    yRes=None,
    resampleAlg="near"
)

# === 3. Open Reprojected Raster ===
ds = gdal.Open(reprojected_raster)
gt = ds.GetGeoTransform()

# Pixel size in meters (EPSG:3857 is in meters)
pixel_width = gt[1]
pixel_height = abs(gt[5])
pixel_area_m2 = pixel_width*pixel_height

print(f"Pixel size in EPSG:3857 (meters):")
print(f"  Width:  {pixel_width:.2f} m")
print(f"  Height: {pixel_height:.2f} m")
print(f"  Area m2: {pixel_width*pixel_height}")


os.remove(reprojected_raster)


df_area = df_count.copy()
for c in raster_cols:
    df_area[c] = df_area[c] * pixel_area_m2

# Save area CSV
df_area.to_csv(area_csv, index=False)

print(f"✅ Areas (hectares) saved to {area_csv}")




```


