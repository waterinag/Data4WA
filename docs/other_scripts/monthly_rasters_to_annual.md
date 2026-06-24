# Convert Monthly Rasters to Annual

This script aggregates a folder of monthly raster files into annual rasters by summing all 12 months of each year. For every year in the specified range, it reads the monthly GeoTIFFs, accumulates their values, and writes out a single annual GeoTIFF.

---


```python
import os
import numpy as np
import rasterio

# Set your paths
input_folder = "WaPOR_ETg_M"      
output_folder = "WaPOR_ETg_A"   

firstyear = 2018
lastyear = 2023  # inclusive

# Create the output folder if it doesn't exist
if not os.path.exists(output_folder):
    os.makedirs(output_folder)

# Loop through each year
for year in range(firstyear, lastyear+1):
    sum_array = None
    profile = None
    
    # Loop through each month (1 to 12)
    for month in range(1, 13):
        # Construct the filename. Adjust this pattern if needed.
        monthly_filename = f"wapor3_etg_{year}_{month:02d}.tif"
        input_path = os.path.join(input_folder, monthly_filename)
        

        # Check if the file exists
        if not os.path.exists(input_path):
            print(f"File {input_path} does not exist, skipping month {month}.")
            continue
        
        # Read the monthly raster data
        with rasterio.open(input_path) as src:
            data = src.read(1)
            
            # Initialize the sum_array and profile on the first valid raster
            if sum_array is None:
                sum_array = np.zeros_like(data, dtype=np.float32)
                profile = src.profile
            
            # Add the monthly data (ensure data is converted to float for accumulation)
            sum_array += data.astype(np.float32)
    
    # Check if any monthly rasters were processed for the year
    if sum_array is not None:
        # Update the metadata profile for output
        profile.update(dtype=rasterio.float32, count=1)
        
        output_path = os.path.join(output_folder, f"wapor3_etg_{year}.tif")
        with rasterio.open(output_path, "w", **profile) as dst:
            dst.write(sum_array, 1)
        print(f"Annual raster for {year} saved to {output_path}")
    else:
        print(f"No monthly rasters found for year {year}.")



```


