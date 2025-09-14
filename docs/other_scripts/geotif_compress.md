# Compress GeoTIFFs
This script batch compresses all GeoTIFF files in a folder using GDAL’s gdal_translate with the DEFLATE compression option. The compressed copies are written to a new output folder, reducing file size while preserving raster values and metadata.

---


```python
import os
import subprocess

input_folder = "input_folder"
output_folder = "output_folder"

os.makedirs(output_folder, exist_ok=True)

for filename in os.listdir(input_folder):
    if filename.endswith(".tif"):
        input_path = os.path.join(input_folder, filename)
        output_filename = filename.replace(".tif", ".tif")
        output_path = os.path.join(output_folder, output_filename)

        command = [
            "gdal_translate",
            "-co", "COMPRESS=DEFLATE",
            input_path,
            output_path
        ]

        print(f"Compressing: {input_path} -> {output_path}")
        subprocess.run(command, check=True)





```


