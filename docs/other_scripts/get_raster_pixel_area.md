# Compute Raster Pixel Area

This script reprojects a raster to EPSG:3857 (meters), extracts its pixel resolution, and calculates the pixel area in square meters.

---


```python
from osgeo import gdal
import os

input_raster = "WaPOR_v2_LULC_2022_cropland.tif"


reprojected_raster = "tem_reprojected_3857.tif"

gdal.Warp(
    destNameOrDestDS=reprojected_raster,
    srcDSOrSrcDSTab=input_raster,
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

print(f"Pixel size in EPSG:3857 (meters):")
print(f"  Width:  {pixel_width:.2f} m")
print(f"  Height: {pixel_height:.2f} m")
print(f"  Area m2: {pixel_width*pixel_height}")


os.remove(reprojected_raster)


```


