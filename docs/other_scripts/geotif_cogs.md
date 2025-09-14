# Convert GeoTIFFs to Cloud Optimized GeoTIFF
This script batch converts standard GeoTIFF files into Cloud Optimized GeoTIFFs (COGs) using gdal_translate. 

---


```python
import os
import subprocess
from osgeo import gdal

input_folder = "input_folder"
output_folder = "output_folder"

os.makedirs(output_folder, exist_ok=True)

for filename in os.listdir(input_folder):
    if filename.endswith(".tif") and not filename.startswith("._"):
        input_path = os.path.join(input_folder, filename)
        output_path = os.path.join(output_folder, filename)

        print(f"Compressing: {input_path} -> {output_path}")

        command = [
            "gdal_translate",
            "-of", "COG", # Output format is Cloud Optimized GeoTIFF.
            "-a_nodata", "-9999", # Assigns nodata value (important for masking).
            "-co", "COMPRESS=LZW", # Uses LZW lossless compression (good general-purpose choice).
            "-co", "BLOCKSIZE=512", # Sets internal tile size (COGs need tiling; 256 or 512 are common).
            "-co", "RESAMPLING=AVERAGE", # For overviews (pyramid levels), resampling method is AVERAGE.
            "-co", "BIGTIFF=IF_SAFER", # Use BigTIFF only if file > 4GB.
            input_path,
            output_path
        ]

        subprocess.run(command, check=True)





```




!!! info "Note"  

    **Compression methods**  
    - `COMPRESS=DEFLATE` → Similar to LZW, often smaller files (slower to read).  
    - `COMPRESS=ZSTD` → Modern compression, faster and better ratios than LZW/DEFLATE (requires GDAL ≥ 3.1).  
    - `COMPRESS=JPEG` → Good for continuous imagery (satellite photos), *lossy* but smaller files.  

    **Tiling & block size**  
    - `BLOCKSIZE=256` → Smaller tiles, better for web maps (faster random access).  
    - `BLOCKSIZE=512` → Larger tiles, better compression efficiency but slower for small reads.  

    **Predictor (for compression efficiency)**  
    - `PREDICTOR=2` → For integer rasters (uses horizontal differencing).  
    - `PREDICTOR=3` → For floating-point rasters (better compression).  

    **Overview (pyramid) settings**  
    - `RESAMPLING=NEAREST` → For categorical data (LULC, classes).  
    - `RESAMPLING=AVERAGE` → For continuous data (climate, elevation).  
    - `RESAMPLING=CUBIC` → Higher-quality resampling for imagery.  

