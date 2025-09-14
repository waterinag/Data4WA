
# Convert NetCDF to GeoTIFF

This script converts monthly grids stored in NetCDF format into individual GeoTIFF rasters. It loops over all NetCDF files in a folder, extracts the primary data variable, enforces CRS (EPSG:4326), sorts months if needed, and exports each monthly slice as a separate GeoTIFF file. 

---


```python
import os
import glob
import rioxarray
import xarray as xr

input_folder = "Monthly Growing Area Grids/2015"
output_folder = "monthly_tifs"
os.makedirs(output_folder, exist_ok=True)

# Get all NetCDF files in the input folder
nc_files = glob.glob(os.path.join(input_folder, "*.nc"))
print(nc_files)


for nc_file in nc_files:
    print(f"Processing: {nc_file}")
    ds = xr.open_dataset(nc_file)

    # Get the primary data variable
    var_name = list(ds.data_vars)[0]
    print("var_name",var_name)
    data = ds[var_name]

    # Enable spatial referencing
    data = data.rio.write_crs("EPSG:4326")

    # Sort months if unordered
    if not all(data['month'][i] <= data['month'][i+1] for i in range(len(data['month']) - 1)):
        data = data.sortby('month')

    for i, month in enumerate(data['month'].values, start=1):
        month_data = data.sel(month=month)

        output_path = os.path.join(
            output_folder,
            f"{os.path.basename(nc_file).replace('.nc', '')}_month_{month:02d}.tif"
        )

        # Flip lat axis if needed (optional, comment out if not required)
        if month_data.latitude[0] < month_data.latitude[-1]:
            month_data = month_data.sel(latitude=slice(None, None, -1))

        # Export to GeoTIFF
        month_data.rio.to_raster(output_path, dtype="float32", nodata=-9999)
        print(f"Saved: {output_path}")

    ds.close()



```


