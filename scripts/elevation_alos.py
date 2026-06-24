import geopandas as gpd
from pystac_client import Client
import planetary_computer as planetary_computer
import requests
from tqdm import tqdm
import os
from osgeo import gdal


geojson_boundary = "/Users/amanchaudhary/Documents/Resources/World_Bank/Jordan/Shapefile/Jordan_L0.geojson"
output_folder = "/Users/amanchaudhary/Documents/Resources/World_Bank/Jordan/alos_dem_30m"


os.makedirs(output_folder, exist_ok=True)


aoi_gdf = gpd.read_file(geojson_boundary)

minx, miny, maxx, maxy = aoi_gdf.total_bounds
bbox = (minx, miny, maxx, maxy)
print(f"Computed bbox from GeoJSON: {bbox}")



# Step 2: Connect to Planetary Computer STAC API
catalog = Client.open("https://planetarycomputer.microsoft.com/api/stac/v1")

# loop over years


# Search WorldCover collection for this year
search = catalog.search(
    collections=["alos-dem"],
    bbox=bbox,
)

try:
    items = list(search.get_items())
except Exception as e:
    raise Exception(f"Error retrieving results: {e}")

items = list(search.get_items())
if not items:
    raise RuntimeError(f"⚠️ No ESA WorldCover tiles found")

total = len(items)
print(items)
processed = 0
print(f"🗂️ Found {total} tile(s)")


# Download tiles
all_tifs = []
for item in tqdm(items, desc=f"Downloading"):
    signed_item = planetary_computer.sign(item)
    print(signed_item)
    print("Available assets:", signed_item.assets.keys())

    # Try standard asset key
    if "data" in signed_item.assets:
        asset_href = signed_item.assets["data"].href
    elif "DSM" in signed_item.assets:
        asset_href = signed_item.assets["DSM"].href
    else:
        raise KeyError(f"No usable asset found for {item.id}: {signed_item.assets.keys()}")

    output_filename = f"{item.id}.tif"
    output_path = os.path.join(output_folder, output_filename)
    all_tifs.append(output_path)

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



print("Merging tiles...")

# Mosaic into VRT
prefix = f"alos_dem_30m"
vrt_path = os.path.join(output_folder, f"{prefix}.vrt")
merged_tif = os.path.join(output_folder, f"{prefix}.tif")
gdal.BuildVRT(vrt_path, all_tifs)
print(f"✅ Created VRT")

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
print(f"🗑️ Cleaned up intermediate files")
