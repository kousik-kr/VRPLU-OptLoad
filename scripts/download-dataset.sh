#!/bin/bash

# Script to download dataset files from Google Drive if not present locally
# Google Drive folder: https://drive.google.com/drive/folders/1amiGMc5Uz92xeuGebwHm2Sj23w_mgN3m?usp=sharing

set -e

DATASET_DIR="dataset"
DATA_RAW_DIR="data/raw"

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "================================================"
echo "  VRPLU-OptLoad Dataset Downloader"
echo "================================================"
echo ""

# Create directories if they don't exist
mkdir -p "$DATASET_DIR"
mkdir -p "$DATA_RAW_DIR"

# Function to check if gdown is installed
check_gdown() {
    # Check if gdown is available in virtual environment
    if [ -f ".venv/bin/gdown" ]; then
        export PATH="$(pwd)/.venv/bin:$PATH"
        return 0
    fi
    
    if ! command -v gdown &> /dev/null; then
        echo -e "${YELLOW}gdown is not installed. Installing...${NC}"
        
        # Try to use virtual environment
        if [ -f ".venv/bin/pip" ]; then
            .venv/bin/pip install gdown && {
                export PATH="$(pwd)/.venv/bin:$PATH"
                echo -e "${GREEN}gdown installed successfully in virtual environment${NC}"
                return 0
            }
        fi
        
        # Try system pip with --user flag
        pip3 install --user gdown || pip install --user gdown || {
            echo -e "${RED}Failed to install gdown. Please install it manually:${NC}"
            echo "  pip install --user gdown"
            echo "  or: pip3 install --user gdown"
            return 1
        }
        echo -e "${GREEN}gdown installed successfully${NC}"
    fi
    return 0
}

# Function to download file from Google Drive
download_file() {
    local file_id="$1"
    local output_file="$2"
    local description="$3"
    
    if [ -f "$output_file" ] && [ -s "$output_file" ]; then
        echo -e "${GREEN}✓${NC} $description already exists: $output_file"
        return 0
    fi
    
    echo -e "${YELLOW}Downloading $description...${NC}"
    
    # Try gdown first
    if command -v gdown &> /dev/null; then
        gdown "https://drive.google.com/uc?id=${file_id}" -O "$output_file" && {
            echo -e "${GREEN}✓${NC} Downloaded $description successfully"
            return 0
        }
    fi
    
    # Fallback to curl
    echo -e "${YELLOW}Trying alternative download method...${NC}"
    curl -L "https://drive.google.com/uc?export=download&id=${file_id}" -o "$output_file" && {
        echo -e "${GREEN}✓${NC} Downloaded $description successfully"
        return 0
    }
    
    # Fallback to wget
    echo -e "${YELLOW}Trying wget...${NC}"
    wget --no-check-certificate "https://drive.google.com/uc?export=download&id=${file_id}" -O "$output_file" && {
        echo -e "${GREEN}✓${NC} Downloaded $description successfully"
        return 0
    }
    
    echo -e "${RED}✗${NC} Failed to download $description"
    return 1
}

# Google Drive file IDs (extract from shared folder links)
# Note: These need to be updated with actual file IDs from the shared folder
# To get file IDs: Right-click file in Google Drive -> Get link -> Extract ID from URL

# Check if we need to download
NODES_FILE="$DATASET_DIR/nodes_285050.txt"
EDGES_FILE="$DATASET_DIR/edges_285050.txt"

NEEDS_DOWNLOAD=false

if [ ! -f "$NODES_FILE" ] || [ ! -s "$NODES_FILE" ]; then
    echo -e "${YELLOW}⚠${NC} nodes_285050.txt not found or empty"
    NEEDS_DOWNLOAD=true
fi

if [ ! -f "$EDGES_FILE" ] || [ ! -s "$EDGES_FILE" ]; then
    echo -e "${YELLOW}⚠${NC} edges_285050.txt not found or empty"
    NEEDS_DOWNLOAD=true
fi

if [ "$NEEDS_DOWNLOAD" = false ]; then
    echo -e "${GREEN}✓ All required dataset files are present${NC}"
    exit 0
fi

echo ""
echo "Dataset files need to be downloaded from Google Drive."
echo "Google Drive folder: https://drive.google.com/drive/folders/1amiGMc5Uz92xeuGebwHm2Sj23w_mgN3m"
echo ""

# Check and install gdown if needed
check_gdown || {
    echo ""
    echo -e "${RED}Unable to install gdown automatically.${NC}"
    echo "Please download the files manually from:"
    echo "  https://drive.google.com/drive/folders/1amiGMc5Uz92xeuGebwHm2Sj23w_mgN3m"
    echo ""
    echo "And place them in: $DATASET_DIR/"
    echo "  - nodes_285050.txt"
    echo "  - edges_285050.txt"
    exit 1
}

echo ""
echo "Attempting to download from Google Drive folder..."
echo ""

# Download the entire folder using gdown
gdown --folder "https://drive.google.com/drive/folders/1amiGMc5Uz92xeuGebwHm2Sj23w_mgN3m" -O "$DATASET_DIR/" --remaining-ok || {
    echo ""
    echo -e "${YELLOW}Automatic download failed. Manual download required.${NC}"
    echo ""
    echo "Please download the files manually from:"
    echo "  https://drive.google.com/drive/folders/1amiGMc5Uz92xeuGebwHm2Sj23w_mgN3m"
    echo ""
    echo "Download these files:"
    echo "  - nodes_285050.txt"
    echo "  - edges_285050.txt"
    echo ""
    echo "And place them in: $(pwd)/$DATASET_DIR/"
    echo ""
    exit 1
}

# Move files from OptLoad subfolder if they exist there
if [ -d "$DATASET_DIR/OptLoad" ]; then
    echo "Moving files from OptLoad subfolder..."
    mv "$DATASET_DIR/OptLoad/"* "$DATASET_DIR/" 2>/dev/null || true
    rmdir "$DATASET_DIR/OptLoad" 2>/dev/null || true
fi

echo ""
echo "================================================"
echo "  Download Status"
echo "================================================"

# Verify downloads
SUCCESS=true

if [ -f "$NODES_FILE" ] && [ -s "$NODES_FILE" ]; then
    SIZE=$(du -h "$NODES_FILE" | cut -f1)
    echo -e "${GREEN}✓${NC} nodes_285050.txt (${SIZE})"
else
    echo -e "${RED}✗${NC} nodes_285050.txt - MISSING or EMPTY"
    SUCCESS=false
fi

if [ -f "$EDGES_FILE" ] && [ -s "$EDGES_FILE" ]; then
    SIZE=$(du -h "$EDGES_FILE" | cut -f1)
    echo -e "${GREEN}✓${NC} edges_285050.txt (${SIZE})"
else
    echo -e "${RED}✗${NC} edges_285050.txt - MISSING or EMPTY"
    SUCCESS=false
fi

echo ""

if [ "$SUCCESS" = true ]; then
    echo -e "${GREEN}All dataset files downloaded successfully!${NC}"
    exit 0
else
    echo -e "${RED}Some files are missing. Please download manually.${NC}"
    exit 1
fi
