"""Test script to check GDAL drivers and HDF subdatasets."""

from pathlib import Path

import rasterio
import rasterio.env

print(f"Rasterio version: {rasterio.__version__}")  # noqa: T201
print(f"GDAL version: {rasterio.__gdal_version__}")  # noqa: T201

# List ALL GDAL drivers
print("\nChecking GDAL driver registry:")  # noqa: T201
try:
    with rasterio.Env() as env:
        # Get all driver codes
        from rasterio._env import get_gdal_config

        print("GDAL_DRIVER_PATH:", get_gdal_config("GDAL_DRIVER_PATH"))  # noqa: T201

        # Check if HDF4 is available
        try:
            test_driver = rasterio.drivers.driver_from_extension(".hdf")
            print(f"HDF extension driver: {test_driver}")  # noqa: T201
        except Exception:
            print("No HDF driver found by extension")  # noqa: T201

except Exception as e:
    print(f"Error checking drivers: {e}")  # noqa: T201

# Try to list subdatasets from the HDF file
print("\n\nAttempting to read subdatasets...")  # noqa: T201

# Try to open one of the downloaded HDF files
hdf_file = Path("data/01_raw/nasa_granules/CHI001/G3639967777-LPCLOUD.hdf")

if hdf_file.exists():
    print(f"\nTrying to open: {hdf_file}")  # noqa: T201
    print(f"File size: {hdf_file.stat().st_size} bytes")  # noqa: T201

    # Try to list subdatasets - HDF4 files MUST be accessed via subdatasets
    try:
        with rasterio.open(str(hdf_file.resolve())) as src:
            print("\nMain dataset opened successfully")  # noqa: T201
            print(f"  Driver: {src.driver}")  # noqa: T201

            # Get subdatasets from tags (HDF4 specific)
            subdatasets = src.subdatasets
            print(f"\n  Subdatasets found: {len(subdatasets)}")  # noqa: T201
            for i, subdataset in enumerate(subdatasets[:5]):  # First 5
                print(f"    {i}: {subdataset}")  # noqa: T201

            # Try to open the LST subdataset (first one)
            if subdatasets:
                lst_subdataset = subdatasets[0]  # LST_Day_1km is the first subdataset
                print(f"\n  Opening LST subdataset: {lst_subdataset}")  # noqa: T201
                with rasterio.open(lst_subdataset) as lst_src:
                    print("  ✓ SUCCESS!")  # noqa: T201
                    print(f"    Shape: {lst_src.shape}")  # noqa: T201
                    print(f"    CRS: {lst_src.crs}")  # noqa: T201
                    print(f"    Bounds: {lst_src.bounds}")  # noqa: T201

                    # Read a small sample
                    data = lst_src.read(1, window=((0, 100), (0, 100)))
                    print(f"    Sample data shape: {data.shape}")  # noqa: T201
                    print(f"    Sample data range: {data.min()} to {data.max()}")  # noqa: T201

    except Exception as e:
        print(f"\nFailed to open main dataset: {e}")  # noqa: T201
        import traceback

        traceback.print_exc()

else:
    print(f"\nFile not found: {hdf_file}")  # noqa: T201
