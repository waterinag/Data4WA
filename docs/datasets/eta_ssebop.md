# Evapotranspiration (SSEBop)
Actual ET (ETa) is produced using the operational Simplified Surface Energy Balance
(SSEBop) model (Senay et al., 2012) for the period 2000 to present. The SSEBop setup is
based on the Simplified Surface Energy Balance (SSEB) approach (Senay et al., 2011, 2013)
with unique parameterization for operational applications. It combines ET fractions generated
from remotely sensed MODIS thermal imagery, acquired every 8 days, with reference ET using
a thermal index approach. The unique feature of the SSEBop parameterization is that it uses
pre-defined, seasonally dynamic, boundary conditions that are unique to each pixel for the
“hot/dry” and “cold/wet” reference points. The original formulation of SSEB is based on the hot
and cold pixel principles of SEBAL (Bastiaanssen et al., 1998) and METRIC (Allen et al., 2007)
models.
---


## Dataset Overview

- **Product**: USGS
- **Source**: [https://edcintl.cr.usgs.gov/downloads/sciweb1/shared/fews/web/global/](https://edcintl.cr.usgs.gov/downloads/sciweb1/shared/fews/web/global/)
- **Format**: GeoTIFF
- **Extent**: Global
- **Data Availability**: v5 = 2003-2022  ; v6 = 2013 - 2024 ; v61 = 2013 - Present
- **Spatial Resolution**: 1000m
- **Temporal Resolution**: Monthly and Annual

---

## Download SSEBop ETa

```python
import requests
import os
import zipfile
from osgeo import gdal

first_year = 2018
last_year = 2019

version='v61'
# Available: 
# v5 = 2003 - 2022
# v6 = 2013 - 2024
# v61 = 2013 - Present

temporal_resolution="Annual" # Annual OR Monthly 
output_folder_path = "/Users/amanchaudhary/Documents/Resources/World_Bank/Jordan"   
geojson_boundary = "/Users/amanchaudhary/Documents/Resources/World_Bank/Jordan/Shapefile/Jordan_L0.geojson" 


output_folder = os.path.join(output_folder_path, f"ssebop_ETa_{version}_{temporal_resolution}") 


os.makedirs(output_folder, exist_ok=True)



filenames = []
if temporal_resolution == "Annual":
    for year in range(first_year, last_year + 1):
        filename = f"y{year}.zip"
        if version=='v5':
            url = f"https://edcintl.cr.usgs.gov/downloads/sciweb1/shared/fews/web/global/yearly/etav5/downloads/{filename}"
        elif version=='v6':
            url = f"https://edcintl.cr.usgs.gov/downloads/sciweb1/shared/fews/web/global/yearly/etav6/downloads/yearly/{filename}"
        elif version=='v61':
            url = f"https://edcintl.cr.usgs.gov/downloads/sciweb1/shared/fews/web/global/yearly/etav61/downloads/yearly/{filename}"

        output_filename = f"ssebop_eta_{year}.tif"
        filenames.append((url,filename, output_filename))


elif temporal_resolution == "Monthly":
    for year in range(first_year, last_year + 1):
        for month in range(1, 13):
            filename = f"m{year}{month:02d}.zip"
            if version=='v5':
                url = f"https://edcintl.cr.usgs.gov/downloads/sciweb1/shared/fews/web/global/monthly/etav5/downloads/{filename}"
            elif version=='v6':
                url = f"https://edcintl.cr.usgs.gov/downloads/sciweb1/shared/fews/web/global/monthly/etav6/downloads/monthly/{filename}"
            elif version=='v61':
                url = f"https://edcintl.cr.usgs.gov/downloads/sciweb1/shared/fews/web/global/monthly/etav61/downloads/monthly/{filename}"

            output_filename = f"ssebop_eta_{year}_{month:02d}.tif"
            filenames.append((url,filename, output_filename))

else:
    raise ValueError("temporal_resolution must be 'Annual' or 'Monthly'")

total = len(filenames)
print(filenames)
print("Total files:",total)



for url,filename, output_filename in filenames:
        zip_path = os.path.join(output_folder, filename)
        print(f"Downloading {filename} ...")

        try:
            response = requests.get(url, stream=True)
            response.raise_for_status()
            with open(zip_path, "wb") as f:
                for chunk in response.iter_content(8192):
                    f.write(chunk)


            # Unzip
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(output_folder)

            # Find the GeoTIFF file (assume one tif per zip)
            tif_files = [f for f in zip_ref.namelist() if f.endswith(".tif")]
            if not tif_files:
                print(f"No .tif found in {filename}")
                continue

            tif_path = os.path.join(output_folder, tif_files[0])
            out_path = os.path.join(output_folder, output_filename)

            warp_options = gdal.WarpOptions(
                cutlineDSName=geojson_boundary,
                cropToCutline=True,
                dstNodata=-9999,

            )
            gdal.Warp(destNameOrDestDS=out_path, srcDSOrSrcDSTab=tif_path, options=warp_options)

            os.remove(tif_path)
            os.remove(zip_path)
            xml_files = [f for f in os.listdir(output_folder) if f.endswith(".xml")]
            for xf in xml_files:
                os.remove(os.path.join(output_folder, xf))

            print(f"✅ Downloaded {filename}")

        except requests.exceptions.RequestException as e:
            print(f"Failed to download {output_filename}: {e}")


```
