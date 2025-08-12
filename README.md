# Galveston County Court Document Scraper - Mac Version

Automated tool for downloading court documents from Galveston County Public Access system, optimized for macOS.

## Quick Start

1. **Install dependencies:**
   ```bash
   pip3 install -r config/requirements.txt
   ```

2. **Install Chrome browser** (required for automation):
   - Download from [Google Chrome](https://www.google.com/chrome/)
   - Or install via Homebrew: `brew install --cask google-chrome`

3. **Run the scraper (choose one option):**
   
   **Simple Launcher (Easiest):**
   ```bash
   ./launch_gui.sh
   ```
   
   **Modern GUI (Recommended for Legal Professionals):**
   ```bash
   python3 court_scraper_gui.py
   ```
   
   **Command Line (Technical Users):**
   ```bash
   python3 court_scraper.py
   ```

4. **Enter a case number** (e.g., `25-CV-0880`)

5. **Choose browser visibility** (command line only - GUI runs headless)

6. **Wait for automatic processing:**
   - Navigates through 7-step court system process
   - Finds and parses all documents
   - Downloads documents to `downloads/[case-number]/`
   - Creates a manifest file

## How It Works

The scraper automates this 7-step process:

1. **Open** Galveston County Public Access website
2. **Click** "Civil and Family Case Records" 
3. **Select** "Case" search type
4. **Enter** case number and search
5. **Click** case number link (first time)
6. **Click** case number link (second time) - *crucial step*
7. **Extract** document links and download files

## 🖥️ Modern GUI Interface

The GUI provides a professional, user-friendly interface designed specifically for legal professionals:

### **Key Features:**
- **📋 Simple Case Entry** - Large text field with format examples and recent cases dropdown
- **📁 Easy Download Location** - Browse button to select where files are saved  
- **📊 Real-Time Progress** - Step-by-step progress bar showing exactly what's happening
- **📝 Detailed Logging** - Clear, friendly progress messages (no technical jargon)
- **✅ Professional Results** - Success/failure messages with file counts and locations
- **🔄 Recent Cases** - Quick access to previously processed case numbers

### **GUI Benefits:**
- **No Technical Knowledge Required** - Point, click, and download
- **Professional Appearance** - Clean interface suitable for law firm environment
- **Error Prevention** - Built-in validation and helpful error messages
- **Progress Transparency** - See exactly what the program is doing at each step
- **Convenient Access** - "Open Folder" button to immediately view downloaded files

### **Perfect for Legal Offices:**
- Paralegals can use it without IT support
- Secretaries can process multiple cases easily  
- Partners can review progress in real-time
- No command line knowledge needed

## Features

- **Automatic Navigation:** No manual clicking required
- **Document Parsing:** Extracts all available court documents
- **Smart Naming:** Uses descriptive filenames with dates
- **Duplicate Prevention:** Skips already downloaded files
- **Progress Tracking:** Shows detailed progress and status
- **Error Handling:** Retries failed navigation automatically
- **Manifest Creation:** Generates file listing with metadata

## File Structure

```
gctx-downloader-mac/
├── court_scraper.py          # Main scraper engine
├── court_scraper_gui.py      # Modern GUI application  
├── launch_gui.sh            # Simple launcher script
├── README.md                # This documentation
├── downloads/               # Downloaded documents
└── config/                # Dependencies and config
    └── requirements.txt
```

## Requirements

- **macOS 10.15+** (Catalina or later)
- **Python 3.8+** - Install via:
  - Homebrew: `brew install python3`
  - [Python.org](https://www.python.org/downloads/)
  - Xcode Command Line Tools: `xcode-select --install`
- **Google Chrome browser** (for Selenium automation)
- **Internet connection**

## Mac-Specific Installation

1. **Install Homebrew** (if not already installed):
   ```bash
   /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
   ```

2. **Install Python and Chrome**:
   ```bash
   brew install python3
   brew install --cask google-chrome
   ```

3. **Clone and setup the project**:
   ```bash
   git clone [repository-url]
   cd gctx-downloader-mac
   pip3 install -r config/requirements.txt
   ```

4. **Make shell scripts executable** (if needed):
   ```bash
   chmod +x launch_gui.sh launch_modern_gui.sh
   ```

## Example Case Numbers

- `25-CV-0880` - Known working case
- `24-CV-1234` - Test different years  
- `23-CV-5678` - Test case variations

## Troubleshooting

### Common Mac Issues

**Python command not found:**
```bash
# Try these alternatives:
python3 court_scraper.py
/usr/bin/python3 court_scraper.py
```

**Permission denied on shell scripts:**
```bash
chmod +x launch_gui.sh launch_modern_gui.sh
```

**Chrome driver issues:**
- Ensure Google Chrome is installed
- Update Chrome to latest version
- Check Chrome version compatibility

**GUI font issues:**
- macOS system fonts (SF Pro) are preferred but fallbacks are included
- Update to macOS 10.15+ for best font support

### General Issues

**Navigation fails:** Try running with visible browser (`y` in CLI mode) to see what's happening

**No documents found:** Case may exist but have no available documents

**Download errors:** Check internet connection and court website status

**Secure documents:** Family court cases often have sealed/protected documents that will show as placeholders

## macOS-Specific Features

- **Native font support**: Uses SF Pro Display/Text fonts when available
- **Spotlight integration**: Downloaded files are indexed by Spotlight
- **Finder integration**: "Open Folder" button opens in Finder
- **Optimized for Retina displays**: High-DPI aware interface