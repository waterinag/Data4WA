# Zonal Statistics by Land Cover Class

This script computes zonal statistics (mean values) of a continuous raster dataset
(e.g., WaPOR RET annual rasters) over each land cover class defined in a
Land Cover Classification (LULC) raster, within polygon boundaries 
(e.g., districts, basins etc.).
---


```python
import geopandas as gpd
import rasterio
from rasterstats import zonal_stats
import pandas as pd
import os
import numpy as np
from rasterio.warp import reproject, Resampling



geojson_boundary = "/Users/amanchaudhary/Documents/Resources/World_Bank/Zambia/Shapefile/Zambia_L2.geojson" 
raster_files_folder = '/Users/amanchaudhary/Desktop/WA_Tool_streamlit/output/Zambia_L0/Data/RET_WaPOR_v3_Annual'
lcc_raster = "/Users/amanchaudhary/Documents/Resources/World_Bank/Zambia/LULC/WaPOR_v2_LULC/WaPOR_v2_LULC_2022_reclass.tif"


output_csv = "/Users/amanchaudhary/Documents/Resources/World_Bank/Zambia/LULC_Stats/RET_annual_LCC_Stats.csv"

# Choose alignment mode: "LULC" (data reprojected to LULC resolution) or 
# "DATA" (LULC reprojected to data raster)

ALIGN_TO = "LULC" # use when coarse lulc or do not take much memory(~100-300m)
# ALIGN_TO = "DATA" # use when lulc raster are too large while loading like (~ ESA LULC 10m)


# Load shapefile
zones_features = gpd.read_file(geojson_boundary)


zones_attr = zones_features.drop(columns="geometry").reset_index(drop=True)
# Load the LCC raster
with rasterio.open(lcc_raster) as lcc_src:
    lcc_data_full = lcc_src.read(1)  # Read the raster band
    lcc_nodata = lcc_src.nodata  # Nodata value
    lcc_affine = lcc_src.transform  # Transform of the LCC raster
    lcc_crs = lcc_src.crs
    lcc_shape = lcc_data_full.shape
    unique_classes = np.unique(lcc_data_full[lcc_data_full != lcc_nodata])  # Get unique land classes
    print("unique_classes",unique_classes)



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

    

# Initialize a list to store results
results = []

# Iterate over raster files in the folder
for filename in os.listdir(raster_files_folder):
    if filename.endswith('.tif'):

        
        print(f"Processing raster for: {filename}")

        raster_file = os.path.join(raster_files_folder, filename)

        if ALIGN_TO == "LULC":
            aligned_data = align_raster_to_lcc(raster_file, lcc_affine, lcc_crs, lcc_shape)
            current_lcc = lcc_data_full
            current_affine = lcc_affine

        elif ALIGN_TO == "DATA":
            aligned_data, current_lcc, current_affine = align_lcc_to_raster(
                raster_file, lcc_data_full, lcc_affine, lcc_crs
            )


        # Iterate over each land cover class
        for lc_class in unique_classes:
            # print(f"Processing land cover class: {lc_class}")

            # Create a mask for the current land cover class
            class_mask = (current_lcc == lc_class)
            class_data = np.where(class_mask, aligned_data, np.nan)

            # Compute zonal statistics
            stats = zonal_stats(
                zones_features.geometry,
                class_data,
                affine=lcc_affine,
                stats=['mean'],
                nodata=np.nan
            )

            # Append results to the list
            for zone_index, stat in enumerate(stats):
                row = zones_attr.iloc[zone_index].to_dict()
                row["LCC"] = int(lc_class)

                ##  Keeps None if the zone has no overlap with raster (useful if you want
                # row[filename] = round(stat["mean"], 2) if stat["mean"] is not None else None

                ##  Replaces missing/NaN values with 0. Useful if you want all zones
                row[filename] = round(stat["mean"], 2) if stat["mean"] is not None else 0

                results.append(row)

# Convert results into a DataFrame
results_df = pd.DataFrame(results)


attr_cols = list(zones_attr.columns) + ["LCC"]
raster_cols = [c for c in results_df.columns if c not in attr_cols]

pivot_df = results_df.pivot_table(
    index=attr_cols,
    values=raster_cols,
    aggfunc="first"
).reset_index()

# Export the entie annual result to an csv file
pivot_df.to_csv(output_csv, index=False)

# Drop attr_cols and LCC columns from numeric cols
year_cols = [c for c in pivot_df.columns if c.endswith(".tif")]

# Compute mean across years
pivot_df["mean_val"] = pivot_df[year_cols].mean(axis=1)

# Pivot: rows = attr_cols, columns = LCC
out_df = pivot_df.pivot_table(
    index=[c for c in pivot_df.columns if c not in ["LCC", "mean_val"] + year_cols],
    columns="LCC",
    values="mean_val"
).reset_index()

out_df = out_df.round(2)

out_df.to_csv(output_csv.replace(".csv", "_all_years_mean.csv"), index=False)


print(f"Zonal statistics for all classes saved to {output_csv}")


```