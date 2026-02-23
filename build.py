"""
Build script for Sub Party using Nuitka.

Usage:
    python build.py          # Build for current platform
    python build.py --clean  # Clean build artifacts first
"""

import os
import shutil
import subprocess
import sys


def clean():
    """Remove previous build artifacts."""
    for d in ["build", "dist", "main.build", "main.dist", "main.onefile-build"]:
        path = os.path.join(os.path.dirname(__file__), d)
        if os.path.isdir(path):
            print(f"Removing {path}")
            shutil.rmtree(path)


def build():
    cmd = [
        sys.executable, "-m", "nuitka",
        "--standalone",
        # "--onefile",
        "--enable-plugin=pyside6",
        "--output-dir=dist",
        "--output-filename=SubParty.exe" if sys.platform == "win32" else "--output-filename=SubParty",
        "--windows-console-mode=disable" if sys.platform == "win32" else "",
        "--company-name=SubParty",
        "--product-name=Sub Party",
        "--product-version=1.0.0",
        "--file-description=LAN File Sharing",
        "--assume-yes-for-downloads",
        "--windows-icon-from-ico=icon.ico",
        "main.py",
    ]
    # filter out empty strings
    cmd = [c for c in cmd if c]

    print(f"Building with: {' '.join(cmd)}")
    print("This may take several minutes...")
    result = subprocess.run(cmd, cwd=os.path.dirname(__file__) or ".")
    if result.returncode == 0:
        print("\nBuild successful! Output: dist/SubParty" + (".exe" if sys.platform == "win32" else ""))
    else:
        print(f"\nBuild failed with exit code {result.returncode}")
    return result.returncode


if __name__ == "__main__":
    if "--clean" in sys.argv:
        clean()
    sys.exit(build())
