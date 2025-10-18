#!/usr/bin/env python3
"""
Script to update MickTrace package version and publish to PyPI.
Usage: python update_package.py 1.0.2
"""

import sys
import subprocess
import re
from pathlib import Path


def update_version(new_version):
    """Update version in all relevant files."""
    # Update pyproject.toml
    pyproject_path = Path("pyproject.toml")
    content = pyproject_path.read_text()
    content = re.sub(r'version = "[^"]*"',
                     f'version = "{new_version}"', content)
    pyproject_path.write_text(content)
    print(f"✅ Updated pyproject.toml to version {new_version}")
    # Update __init__.py
    init_path = Path("src/micktrace/__init__.py")
    content = init_path.read_text()
    content = re.sub(
        r'__version__ = "[^"]*"', f'__version__ = "{new_version}"', content
    )
    init_path.write_text(content)
    print(f"✅ Updated __init__.py to version {new_version}")
    print(f"🎯 Version updated to {new_version}")
    print("📝 Don't forget to update CHANGELOG.md manually!")


def build_and_upload():
    """Build and upload package to PyPI."""
    subprocess.run(
        [
            "powershell",
            "-Command",
            "Remove-Item -Path 'dist', 'build', '*.egg-info' -Recurse -Force -ErrorAction SilentlyContinue",
        ],
        check=False,
    )
    print("🧹 Cleaned previous builds")
    # Build package
    result = subprocess.run(["python", "-m", "build"],
                            capture_output=True, text=True)
    if result.returncode != 0:
        print(f"❌ Build failed: {result.stderr}")
        return False
    print("📦 Package built successfully")
    # Upload to PyPI
    print("🚀 Uploading to PyPI...")
    result = subprocess.run(
        ["python", "-m", "twine", "upload", "dist/*", "--username", "__token__"]
    )
    if result.returncode == 0:
        print("🎉 Package uploaded successfully!")
        return True
    else:
        print("❌ Upload failed")
        return False


def main():
    if len(sys.argv) != 2:
        print("Usage: python update_package.py <new_version>")
        print("Example: python update_package.py 1.0.2")
        sys.exit(1)
    new_version = sys.argv[1]
    # Validate version format
    if not re.match(r"^\d+\.\d+\.\d+$", new_version):
        print("❌ Invalid version format. Use: Major.Minor.Patch (e.g., 1.0.2)")
        sys.exit(1)
    print(f"🔄 Updating MickTrace to version {new_version}")
    # Update version
    update_version(new_version)
    # Ask for confirmation
    response = input(
        f"\n📝 Please update CHANGELOG.md with changes for v{new_version}\nReady to build and upload? (y/N): "
    )
    if response.lower() != "y":
        print("⏸️ Update cancelled. Run again when ready.")
        sys.exit(0)
    # Build and upload
    if build_and_upload():
        print(f"\n🎉 MickTrace v{new_version} is now live on PyPI!")
        print(
            f"📦 Users can now install with: pip install micktrace=={new_version}")
    else:
        print("\n❌ Update failed. Check errors above.")


if __name__ == "__main__":
    main()
