# Clip Raster to Boundary
This script iterates over all raster files in a folder and clips them to a given boundary (GeoJSON) using gdal.Warp. The output rasters are cropped, compressed (LZW), tiled, and assigned a nodata value. 

---


```python
import os
from osgeo import gdal

# Paths
input_folder = "WaPOR_ETb_A"      
output_folder = "WaPOR_ETb_A_clip"   
geojson_boundary = "AFG_boundary.geojson" 

# Create output folder if missing
os.makedirs(output_folder, exist_ok=True)

# List all tif files in input folder
tif_files = [f for f in os.listdir(input_folder) if f.endswith(".tif")]

print(f"🗂️ Found {len(tif_files)} TIFF files")

for filename in tif_files:
    input_path = os.path.join(input_folder, filename)
    output_path = os.path.join(output_folder, filename)


    # Step 2: Clip scaled raster with AOI
    warp_options = gdal.WarpOptions(
        cutlineDSName=geojson_boundary,
        cropToCutline=True,
        dstNodata=-9999,
        format="GTiff",
        creationOptions=["COMPRESS=LZW", "TILED=YES", "BIGTIFF=YES"]
    )
    gdal.Warp(destNameOrDestDS=output_path, srcDSOrSrcDSTab=input_path, options=warp_options)


    print(f"✅ Processed {filename}: scaled by 0.1 & clipped → {output_path}")



```


