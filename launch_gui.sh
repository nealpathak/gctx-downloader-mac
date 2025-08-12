#!/bin/bash
# Galveston County Court Document Scraper - GUI Launcher
# Simple launcher script for legal professionals

echo "🏛️  Galveston County Court Document Scraper"
echo "=============================================="
echo ""

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "📁 Working directory: $SCRIPT_DIR"
echo ""

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: Python 3 is not installed."
    echo "Please install Python 3 first:"
    echo "  brew install python3"
    echo ""
    read -p "Press Enter to exit..."
    exit 1
fi

# Check if required packages are installed
echo "🔍 Checking dependencies..."
if ! python3 -c "import customtkinter" &> /dev/null; then
    echo "📦 Installing required packages..."
    pip3 install -r config/requirements.txt
    echo ""
fi

# Verify files exist
if [ ! -f "court_scraper_gui.py" ]; then
    echo "❌ Error: court_scraper_gui.py not found in $SCRIPT_DIR"
    echo "Please make sure you're running this script from the correct directory."
    echo ""
    read -p "Press Enter to exit..."
    exit 1
fi

# Launch the GUI
echo "🚀 Starting Court Document Scraper GUI..."
echo ""
python3 court_scraper_gui.py

echo ""
echo "GUI closed. Press Enter to exit..."
read