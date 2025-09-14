# Zonal Statistics over Cropland Areas

This script calculates zonal statistics (mean values) of continuous raster data 
(e.g., WaPOR AETI monthly) restricted to cropland areas within administrative 
polygons (e.g., districts, basins etc). It outputs a table of mean 
values for each zone and each raster file, but only for pixels that belong 
to the cropland class in a Land Cover raster.
---


```python
import geopandas as gpd
import rasterio
from rasterstats import zonal_stats
import pandas as pd
import os
import numpy as np
from rasterio.warp import reproject, Resampling

# ---------------- CONFIG ----------------
geojson_boundary = "/Users/amanchaudhary/Documents/Resources/World_Bank/Zambia/Shapefile/Zambia_L2.geojson" 
raster_files_folder = "/Users/amanchaudhary/Documents/Resources/World_Bank/Zambia/AETI_WaPOR_v3_L1_M"

lcc_raster = "/Users/amanchaudhary/Documents/Resources/World_Bank/Zambia/LULC/WaPOR_v2_LULC/WaPOR_v2_LULC_2022_cropland.tif"
cropland_class = 40

output_csv = "/Users/amanchaudhary/Documents/Resources/World_Bank/Zambia/LULC_Stats/WaPOR_Cropland_AETI_M.csv"

# Choose alignment mode: "LULC" (data reprojected to LULC resolution) or 
# "DATA" (LULC reprojected to data raster)

ALIGN_TO = "LULC" # use when coarse lulc or do not take much memory(~100-300m)
# ALIGN_TO = "DATA" # use when lulc raster are too large while loading like (~ ESA LULC 10m)


# -----------------------------------------

# Load shapefile
zones_features = gpd.read_file(geojson_boundary)
zones_attr = zones_features.drop(columns="geometry").reset_index(drop=True)

# Load LULC raster (full resolution, e.g., 10 m)
with rasterio.open(lcc_raster) as lcc_src:
    lcc_data_full = lcc_src.read(1)  # Read the raster band
    lcc_nodata = lcc_src.nodata  # Nodata value
    lcc_affine = lcc_src.transform  # Transform of the LCC raster
    lcc_crs = lcc_src.crs
    lcc_shape = lcc_data_full.shape
    unique_classes = np.unique(lcc_data_full[lcc_data_full != lcc_nodata])  # Get unique land classes
    print("unique_classes",unique_classes)

print("✅ Loaded ESA LULC raster")

# ---------------- FUNCTION ----------------

# Function to reproject and resample a raster
def align_raster_to_lcc(src_raster, lcc_transform, lcc_crs, lcc_shape):
    """Reproject a raster to the LCC grid and return float32 with NaNs for NoData."""
    with rasterio.open(src_raster) as src:
        data = src.read(1).astype("float32")  # <-- ensure float
        data_nodata = src.nodata
        if data_nodata is not None:
            data[data == data_nodata] = np.nan  # safe now (float array)

        # Initialize destination as NaNs (float)
        aligned_data = np.full(lcc_shape, np.nan, dtype="float32")

        # TBP is continuous → bilinear is appropriate. Use nearest for categorical rasters.
        reproject(
            source=data,
            destination=aligned_data,
            src_transform=src.transform,
            src_crs=src.crs,
            dst_transform=lcc_transform,
            dst_crs=lcc_crs,
            resampling=Resampling.bilinear
        )
        return aligned_data


def align_lcc_to_raster(src_raster, lcc_data_full, lcc_transform, lcc_crs):
    """Reproject LULC raster to match data raster grid"""
    with rasterio.open(src_raster) as src:
        dst_shape = (src.height, src.width)
        dst_transform = src.transform
        dst_crs = src.crs

        # Prepare destination
        lulc_resampled = np.full(dst_shape, 0, dtype=np.int16)

        reproject(
            source=lcc_data_full,
            destination=lulc_resampled,
            src_transform=lcc_transform,
            src_crs=lcc_crs,
            dst_transform=dst_transform,
            dst_crs=dst_crs,
            resampling=Resampling.nearest  # keep categorical
        )

        data = src.read(1).astype("float32")
        if src.nodata is not None:
            data[data == src.nodata] = np.nan

        return data, lulc_resampled, dst_transform
# ------------------------------------------

results = []

# Iterate over AETI rasters
for filename in sorted(os.listdir(raster_files_folder)):
    if filename.endswith(".tif"):
        raster_file = os.path.join(raster_files_folder, filename)
        print(f"Processing raster: {filename}")

        if ALIGN_TO == "LULC":
            aligned_data = align_raster_to_lcc(raster_file, lcc_affine, lcc_crs, lcc_shape)
            current_lcc = lcc_data_full
            current_affine = lcc_affine

        elif ALIGN_TO == "DATA":
            aligned_data, current_lcc, current_affine = align_lcc_to_raster(
                raster_file, lcc_data_full, lcc_affine, lcc_crs
            )

        class_mask = (current_lcc == cropland_class)
        class_data = np.where(class_mask, aligned_data, np.nan)
        

        # Compute zonal stats
        stats = zonal_stats(
            zones_features.geometry,
            class_data,
            affine=lcc_affine,
            stats=['mean'],
            nodata=np.nan
        )

        # Save results
        for zone_index, stat in enumerate(stats):
            row = zones_attr.iloc[zone_index].to_dict()
            # row["LCC"] = int(cropland_class)
            ##  Keeps None if the zone has no overlap with raster (useful if you want
            # row[filename] = round(stat["mean"], 2) if stat["mean"] is not None else None

            ##  Replaces missing/NaN values with 0. Useful if you want all zones
            row[filename] = round(stat["mean"], 2) if stat["mean"] is not None else 0

            results.append(row)


# Convert to DataFrame
results_df = pd.DataFrame(results)


# attr_cols = list(zones_attr.columns) + ["LCC"]
attr_cols = list(zones_attr.columns)
raster_cols = [c for c in results_df.columns if c not in attr_cols]


pivot_df = results_df.pivot_table(
    index=attr_cols,
    values=raster_cols,
    aggfunc="first"
).reset_index()

# Save to Excel
pivot_df.to_csv(output_csv, index=False)
print(f"✅ Zonal statistics saved to {output_csv}")





```


