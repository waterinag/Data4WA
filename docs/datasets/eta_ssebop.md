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

## Download Monthly ETa (SSEBop)


```python
import requests
import os
import zipfile
from osgeo import gdal


firstyear = 2018
lastyear = 2020

output_folder = "ssebop_eta_monthly"   
geojson_boundary = "Zambia_L0.geojson" 

version='v5'
# Available versions:  
# v5 = 2003 - 2022
# v6 = 2013 - 2024
# v61 = 2013 - Present

os.makedirs(output_folder, exist_ok=True)

for year in range(firstyear, lastyear+1):
        for month in range(1, 13):
             
            filename = f"m{year}{month:02d}.zip"
            out_filename = f"ssebop_eta_{year}_{month:02d}.tif"
            if version=='v5':
                url = f"https://edcintl.cr.usgs.gov/downloads/sciweb1/shared/fews/web/global/monthly/etav5/downloads/{filename}"
            elif version=='v6':
                url = f"https://edcintl.cr.usgs.gov/downloads/sciweb1/shared/fews/web/global/monthly/etav6/downloads/monthly/{filename}"
            elif version=='v61':
                url = f"https://edcintl.cr.usgs.gov/downloads/sciweb1/shared/fews/web/global/monthly/etav61/downloads/monthly/{filename}"
            
            else:
                print("❌ Error: Unsupported version")
                continue

            zip_path = os.path.join(output_folder, filename)

            print(f"Downloading {filename}")
            
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
                tif_files = [f for f in os.listdir(output_folder) if f.endswith(".tif") and f.startswith(f"m{year}{month:02d}")]
                if not tif_files:
                    print(f"No .tif found in {filename}")
                    continue



                tif_path = os.path.join(output_folder, tif_files[0])
                out_path = os.path.join(output_folder, out_filename)

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
                print(f"Failed to download {out_filename}: {e}")



```

## Download Annual ETa (SSEBop)


```python
import requests
import os
import zipfile
from osgeo import gdal

firstyear = 2013
lastyear = 2022

output_folder = "ssebop_eta_annual"   
geojson_boundary = "Zambia_L0.geojson" 

version='v61'
# Available: 
# v5 = 2003 - 2022
# v6 = 2013 - 2024
# v61 = 2013 - Present


os.makedirs(output_folder, exist_ok=True)


for year in range(firstyear, lastyear+1):

        filename = f"y{year}.zip"

        out_filename = f"ssebop_eta_{year}.tif"

        if version=='v5':
            url = f"https://edcintl.cr.usgs.gov/downloads/sciweb1/shared/fews/web/global/yearly/etav5/downloads/{filename}"
        elif version=='v6':
            url = f"https://edcintl.cr.usgs.gov/downloads/sciweb1/shared/fews/web/global/yearly/etav6/downloads/yearly/{filename}"
        elif version=='v61':
            url = f"https://edcintl.cr.usgs.gov/downloads/sciweb1/shared/fews/web/global/yearly/etav61/downloads/yearly/{filename}"

            
        zip_path = os.path.join(output_folder, filename)

        print(f"Downloading {filename} from {url} ...")
        
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
            tif_files = [f for f in os.listdir(output_folder) if f.endswith(".tif") and f.startswith(f"y{year}")]
            if not tif_files:
                print(f"No .tif found in {filename}")
                continue

            tif_path = os.path.join(output_folder, tif_files[0])
            out_path = os.path.join(output_folder, out_filename)

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
            print(f"Failed to download {out_filename}: {e}")




```






