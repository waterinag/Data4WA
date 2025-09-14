
# ESA LULC 10m
The European Space Agency (ESA) WorldCover 10 m 2021 product provides a global land cover map for 2021 at 10 m resolution based on Sentinel-1 and Sentinel-2 data. The WorldCover product comes with 11 land cover classes and has been generated in the framework of the ESA WorldCover project, part of the 5th Earth Observation Envelope Programme (EOEP-5) of the European Space Agency.

---

## Dataset Overview

- **Product**: ESA LULC
- **Source**: [https://esa-worldcover.org/en](https://esa-worldcover.org/en)
- **Format**: GeoTIFF
- **Extent**: Global
- **Data Availability**: 2020-2021
- **Spatial Resolution**: 10m
- **Temporal Resolution**: Annual


---


## Download ESA LULC 10m Data

```python

import geopandas as gpd
from pystac_client import Client
import planetary_computer as planetary_computer
import requests
from tqdm import tqdm
import os
from osgeo import gdal


geojson_boundary = "/Users/amanchaudhary/Documents/Resources/World_Bank/Jordan/Shapefile/Jordan_L0.geojson" 
output_folder = "/Users/amanchaudhary/Documents/Resources/World_Bank/Jordan/ESA_LULC"   
os.makedirs(output_folder, exist_ok=True)

year=2021 # 2020 or 2021

aoi_gdf = gpd.read_file(geojson_boundary)

minx, miny, maxx, maxy = aoi_gdf.total_bounds
bbox = (minx, miny, maxx, maxy)
print(f"Computed bbox from GeoJSON: {bbox}")



# Step 2: Connect to Planetary Computer STAC API
catalog = Client.open("https://planetarycomputer.microsoft.com/api/stac/v1")

# loop over years

prefix = f"ESA_WorldCover_10m_{year}"
print(f"\n📅 Processing year: {year}")

# Search WorldCover collection for this year
search = catalog.search(
    collections=["esa-worldcover"],
    bbox=bbox,
    datetime=f"{year}-01-01/{year}-12-31",
)

try:
    items = list(search.get_items())
except Exception as e:
    raise Exception(f"Error retrieving results for {year}: {e}")

items = list(search.get_items())
if not items:
    raise RuntimeError(f"⚠️ No ESA WorldCover tiles found for {year}")

total = len(items)
print(items)
processed = 0
print(f"🗂️ Found {total} tile(s) for {year}")


# Download tiles
all_tifs = []
for item in tqdm(items, desc=f"Downloading {year}"):
    signed_item = planetary_computer.sign(item)
    asset_href = signed_item.assets["map"].href
    output_filename = f"{item.id}.tif"
    output_path = os.path.join(output_folder, output_filename)



    if os.path.exists(output_path):
        print(f"✅ {output_path} already exists, skipping...")
        continue


    else:
        with requests.get(asset_href, stream=True) as r:
            r.raise_for_status()
            with open(output_path, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)


    # 👇 always append
    all_tifs.append(output_path)


print("Merging tiles")

# Mosaic into VRT
vrt_path = os.path.join(output_folder, f"{prefix}.vrt")
merged_tif = os.path.join(output_folder, f"{prefix}.tif")
gdal.BuildVRT(vrt_path, all_tifs)
print(f"✅ Created VRT for {year}")

# Clip to AOI
gdal.Warp(
    merged_tif,
    vrt_path,
    cutlineDSName=geojson_boundary,
    cropToCutline=True,
    dstNodata=0,
    format="GTiff",
    creationOptions=["COMPRESS=LZW", "TILED=YES", "BIGTIFF=YES"],
)
print(f"🎉 Final clipped raster saved: {merged_tif}")

# cleanup tiles + vrt
for tif in all_tifs:
    os.remove(tif)
if os.path.exists(vrt_path):
    os.remove(vrt_path)
print(f"🗑️ Cleaned up intermediate files for {year}")



```

---

