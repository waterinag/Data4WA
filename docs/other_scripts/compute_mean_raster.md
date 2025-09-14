# Compute Multi-Temporal Mean Raster
This script calculates the multi-year mean from a stack of annual raster files. It reads all GeoTIFFs in a folder, handles nodata values, and processes the rasters block by block to avoid memory issues with large datasets. The result is a single GeoTIFF representing the average across all input years.

---


```python
import os
import numpy as np
from osgeo import gdal

# Input and output paths
raster_folder = 'WaPOR_v3_AETI_Annual'
mean_raster_path = 'WaPOR_v3_AETI_Mean_2018_24.tif'

# List input rasters
file_paths = [
    os.path.join(raster_folder, f)
    for f in os.listdir(raster_folder)
    if f.endswith('.tif') and not f.startswith('._')
]

file_paths.sort()  # optional, for consistent order

# Open first raster for shape
ds0 = gdal.Open(file_paths[0])
cols = ds0.RasterXSize
rows = ds0.RasterYSize
band_count = len(file_paths)
gt = ds0.GetGeoTransform()
proj = ds0.GetProjection()
nodata = ds0.GetRasterBand(1).GetNoDataValue()
ds0 = None

# Create output raster
driver = gdal.GetDriverByName('GTiff')
out_ds = driver.Create(mean_raster_path, cols, rows, 1, gdal.GDT_Float32, options=['COMPRESS=DEFLATE'])
out_ds.SetGeoTransform(gt)
out_ds.SetProjection(proj)
out_band = out_ds.GetRasterBand(1)
out_band.SetNoDataValue(-9999)

# Process block by block
block_size = 512
for y in range(0, rows, block_size):
    ysize = min(block_size, rows - y)
    for x in range(0, cols, block_size):
        xsize = min(block_size, cols - x)
        block_stack = []

        for fpath in file_paths:
            ds = gdal.Open(fpath)
            data = ds.GetRasterBand(1).ReadAsArray(x, y, xsize, ysize).astype(np.float32)
            ds = None
            if nodata is not None:
                data[data == nodata] = np.nan
            block_stack.append(data)

        block_stack = np.array(block_stack)
        block_mean = np.nanmean(block_stack, axis=0)

        block_mean[np.isnan(block_mean)] = -9999
        out_band.WriteArray(block_mean, x, y)

# Finalize
out_band.FlushCache()
out_ds = None

print("✅ Mean raster created efficiently using GDAL!")




```


