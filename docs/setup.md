# ⚙️ Environment Setup for Dataset Download

To download and process datasets with Data4WA, you need a Python environment configured with common geospatial libraries such as GDAL, Rasterio, Xarray, and others.


### 1: Install Conda (Recommended)

Conda is a cross-platform environment manager that makes it easy to install geospatial libraries like GDAL.

#### Windows

1. Download the **Miniconda installer**:  
   👉 [Miniconda Windows 64-bit](https://docs.conda.io/en/latest/miniconda.html#windows-installers)
2. Run the installer and choose “Add Miniconda to PATH” during setup.
3. After installation, open **Anaconda Prompt** or **Command Prompt** and test:

```bash
conda --version
```

---

#### MacOS OS

1. Download the installer for macOS from:  
   👉 [Miniconda macOS](https://docs.conda.io/en/latest/miniconda.html#macos-installers)

2. Run the installer


3. Restart terminal and verify:

```bash
conda --version
```

---

### 2: Create a Conda Environment

```bash
conda create --name data4wa_env python=3.10
conda activate data4wa_env
```

---

### 3: Install GDAL and Geospatial Libraries

Use the `conda-forge` channel:

```bash
conda install -c conda-forge "gdal=3.10.*" libgdal-jp2openjpeg  
```

Verify GDAL installation:

```bash
gdalinfo --version
```


Then install required Python libraries:

```bash
pip install pandas tqdm geopandas numpy xarray rioxarray rasterio netCDF4 requests beautifulsoup4  earthengine-api geemap planetary-computer pystac-client
```


### 4: Enable Jupyter Notebook Support (Optional)

```bash
conda install -c conda-forge notebook ipykernel
python -m ipykernel install --user --name=data4wa_env --display-name "Python (data4wa_env)"

```
> To select the environment kernel in Jupyter:
Kernel → Change Kernel → Python (data4wa_env)


Optional Cleanup: If you ever want to remove the kernel, use:
```bash
jupyter kernelspec uninstall data4wa_env
```


---


