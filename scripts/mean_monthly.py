#!/opt/anaconda3/envs/gdal/bin/python
import os
import glob
import numpy as np
import rasterio

first_year = 2018
last_year = 2025
prefix = "AETI_"
monthly_rasters = "AETI_WaPORv3_L1_Monthly"
mean_monthly_rasters = "AETI_WaPORv3_L1_mean_Monthly"

os.makedirs(mean_monthly_rasters, exist_ok=True)

for month in range(1, 13):
    files = []
    for year in range(first_year, last_year + 1):
        glob_pattern = os.path.join(monthly_rasters, f"{prefix}{year}{month:02d}*.tif")
        matched = glob.glob(glob_pattern)
        if matched:
            files.append(matched[0])
        else:
            print(f"  WARNING: no file found for {year}-{month:02d}")

    if not files:
        print(f"Month {month:02d}: no files found, skipping.")
        continue

    print(f"Month {month:02d}: averaging {len(files)} rasters...")

    arrays = []
    profile = None
    for f in files:
        with rasterio.open(f) as src:
            if profile is None:
                profile = src.profile.copy()
                nodata = src.nodata
            data = src.read(1).astype(np.float32)
            if nodata is not None:
                data[data == nodata] = np.nan
            arrays.append(data)

    stack = np.stack(arrays, axis=0)
    mean = np.nanmean(stack, axis=0)

    profile.update(dtype=rasterio.float32, count=1, nodata=-9999)

    out_path = os.path.join(mean_monthly_rasters, f"{prefix}mean_month_{month:02d}.tif")
    with rasterio.open(out_path, "w", **profile) as dst:
        out = np.where(np.isnan(mean), -9999, mean).astype(np.float32)
        dst.write(out, 1)

    print(f"  Saved: {out_path}")

print("Done. 12 mean monthly rasters written to:", mean_monthly_rasters)
