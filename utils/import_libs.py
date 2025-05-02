import os, sys, importlib
from typing import Dict, Any


def import_libs(libs_path: str = "libs", verbose: bool = False) -> Dict[str, Any]:
    """
    Dynamically imports all packages contained in a 'libs' folder

    Args:
        libs_path: Path to the libs directory (default: 'libs')
        verbose: Whether to print import information (default: False)

    Returns:
        Dictionary mapping package names to imported package modules

    Example:
        # Import all packages from the libs directory
        packages = import_libs_packages()

        # Use an imported package
        if 'kronos' in packages:
            kronos = packages['kronos']

        logger = kronos.Logger()
        logger.info("Using dynamically imported Kronos")
    """
    # Get absolute path to the libs directory
    base_dir = os.path.abspath(os.path.dirname(__file__))
    full_libs_path = os.path.join(base_dir, libs_path)

    if not os.path.exists(full_libs_path):
        if verbose:
            print(f"Warning: Libs directory '{full_libs_path}' does not exist")
        return {}

    # Add the libs directory to Python's import path
    if full_libs_path not in sys.path:
        sys.path.insert(0, full_libs_path)

    imported_packages = {}

    # Get all subdirectories in the libs directory
    for item in os.listdir(full_libs_path):
        package_path = os.path.join(full_libs_path, item)

        # Check if it's a directory and contains __init__.py
        if (os.path.isdir(package_path) and
                os.path.exists(os.path.join(package_path, "__init__.py"))):
            try:
                # Attempt to import the package
                if verbose:
                    print(f"Importing package: {item}")

                package = importlib.import_module(item)
                imported_packages[item] = package

                if verbose:
                    print(f"Successfully imported: {item}")

            except ImportError as e:
                if verbose:
                    print(f"Failed to import {item}: {str(e)}")

    if verbose:
        print(f"Imported {len(imported_packages)} packages: {', '.join(imported_packages.keys())}")

    return imported_packages