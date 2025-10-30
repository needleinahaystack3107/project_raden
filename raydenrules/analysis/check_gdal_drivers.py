# noqa: T201
"""Check GDAL drivers available"""

import rasterio

print(f"Rasterio version: {rasterio.__version__}")  # noqa: T201
print(f"GDAL version: {rasterio.__gdal_version__}\n")  # noqa: T201

# Get all available drivers
with rasterio.Env() as env:
    drivers = rasterio.drivers.raster_driver_extensions()
    print(f"Total drivers: {len(drivers)}\n")  # noqa: T201

    # Look for HDF
    hdf_found = False
    for driver_name in sorted(drivers.keys()):
        if "HDF" in driver_name.upper():
            print(f"✓ Found: {driver_name}")  # noqa: T201
            hdf_found = True

    if not hdf_found:
        print("❌ NO HDF DRIVERS FOUND!")  # noqa: T201
        print("\nChecking all drivers for HDF:")  # noqa: T201
        for driver_name in sorted(drivers.keys())[:50]:
            print(f"  - {driver_name}")  # noqa: T201
