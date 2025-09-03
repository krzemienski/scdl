#!/bin/bash

# SCDL Threaded Version Installation Script
# This script installs the multi-threaded version of scdl as 'scdl-threaded'

set -e  # Exit on error

echo "=========================================="
echo "SCDL Multi-Threaded Version Installation"
echo "=========================================="

# Check if we're in the right directory
if [ ! -f "setup.py" ] || [ ! -d "scdl" ]; then
    echo "❌ Error: This script must be run from the scdl project root directory"
    exit 1
fi

# Check current branch
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
echo "📍 Current branch: $CURRENT_BRANCH"

if [ "$CURRENT_BRANCH" != "threading" ]; then
    echo "⚠️  Warning: Not on 'threading' branch. Current branch is '$CURRENT_BRANCH'"
    read -p "Do you want to switch to the threading branch? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        git checkout threading
    fi
fi

# Create a temporary copy of the setup.py with modified name
echo "📦 Preparing installation..."
cp setup.py setup_threaded.py

# Modify the setup_threaded.py to use 'scdl-threaded' as the package name
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    sed -i '' 's/name="scdl"/name="scdl-threaded"/' setup_threaded.py
    sed -i '' 's/"scdl = scdl.scdl:main"/"scdl-threaded = scdl.scdl:main"/' setup_threaded.py
else
    # Linux
    sed -i 's/name="scdl"/name="scdl-threaded"/' setup_threaded.py
    sed -i 's/"scdl = scdl.scdl:main"/"scdl-threaded = scdl.scdl:main"/' setup_threaded.py
fi

# Check if pip is available
if ! command -v pip3 &> /dev/null; then
    echo "❌ Error: pip3 not found. Please install Python 3 and pip3"
    exit 1
fi

# Uninstall any existing scdl-threaded installation
echo "🔄 Removing any existing scdl-threaded installation..."
pip3 uninstall -y scdl-threaded 2>/dev/null || true

# Install the threaded version
echo "📦 Installing scdl-threaded..."
pip3 install --editable . --force-reinstall

# Clean up
rm setup_threaded.py

# Verify installation
echo ""
echo "✅ Verifying installation..."
if command -v scdl-threaded &> /dev/null; then
    echo "✅ scdl-threaded successfully installed!"
    echo ""
    echo "📍 Installation location: $(which scdl-threaded)"
    echo ""
    echo "🎯 Usage examples:"
    echo "  scdl-threaded -l <soundcloud_url> --threads 5"
    echo "  scdl-threaded -l <playlist_url> --threads 10"
    echo "  scdl-threaded --help"
    echo ""
    echo "ℹ️  Note: The threading feature is hardcoded to use 5 threads by default"
    echo "    in the current implementation (line 445 in scdl.py)"
else
    echo "❌ Installation failed. Please check the error messages above."
    exit 1
fi

echo "=========================================="
echo "Installation complete!"
echo "=========================================="