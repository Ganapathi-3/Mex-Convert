#!/bin/bash
#
# Citrus Converter — Installation Script for Debian 12 (Bookworm)
#
# Usage:
#   chmod +x install.sh
#   ./install.sh
#

set -e

ORANGE='\033[0;33m'
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color
BOLD='\033[1m'

echo -e "${ORANGE}${BOLD}"
echo "  🍊 Citrus Converter — Installer"
echo "  ================================"
echo -e "${NC}"

# Check if running on Debian-based system
if ! command -v apt &> /dev/null; then
    echo -e "${RED}❌ This installer requires apt (Debian/Ubuntu).${NC}"
    exit 1
fi

echo -e "${BOLD}Step 1: Installing system dependencies...${NC}"
echo "This may require sudo password."
echo ""

sudo apt update -qq

# Core dependencies
PACKAGES=(
    # Python and Qt
    python3
    python3-pip
    # Media conversion
    ffmpeg
    # Image processing
    imagemagick
    # Document conversion
    pandoc
    # Office document support
    libreoffice-core
    libreoffice-writer
    # Archive support
    p7zip-full
    # PDF tools
    qpdf
    ghostscript
    # Metadata
    libimage-exiftool-perl
)

echo -e "Installing: ${PACKAGES[*]}"
echo ""

sudo apt install -y "${PACKAGES[@]}"

echo ""
echo -e "${GREEN}✅ System dependencies installed.${NC}"
echo ""

echo -e "${BOLD}Step 2: Configuring ImageMagick policy...${NC}"
# ImageMagick's default policy on Debian blocks PDF operations.
# We need to allow it for PDF conversion.
POLICY_FILE="/etc/ImageMagick-6/policy.xml"
if [ -f "$POLICY_FILE" ]; then
    # Check if PDF is blocked
    if grep -q 'pattern="PDF"' "$POLICY_FILE" && grep -q 'rights="none".*pattern="PDF"' "$POLICY_FILE"; then
        echo "  Updating ImageMagick policy to allow PDF operations..."
        sudo sed -i 's/rights="none" pattern="PDF"/rights="read|write" pattern="PDF"/g' "$POLICY_FILE"
        echo -e "  ${GREEN}✅ ImageMagick PDF policy updated.${NC}"
    else
        echo -e "  ${GREEN}✅ ImageMagick PDF policy already configured.${NC}"
    fi
else
    echo "  ⚠️  ImageMagick policy file not found (non-critical)."
fi

echo ""
echo -e "${BOLD}Step 3: Installing Citrus Converter...${NC}"

# Install the app
cd "$(dirname "$0")"
pip3 install -e . --break-system-packages 2>/dev/null || pip3 install -e .

echo ""
echo -e "${GREEN}✅ Citrus Converter installed.${NC}"
echo ""

echo -e "${BOLD}Step 4: Creating desktop entry...${NC}"

DESKTOP_DIR="$HOME/.local/share/applications"
mkdir -p "$DESKTOP_DIR"
AUTOSTART_DIR="$HOME/.config/autostart"
mkdir -p "$AUTOSTART_DIR"
CITRUS_EXEC="$(command -v citrus-converter)"

cat > "$DESKTOP_DIR/citrus-converter.desktop" << EOF
[Desktop Entry]
Name=Citrus Converter
Comment=Free, offline file conversion tool
Exec=$CITRUS_EXEC %F
Icon=citrus-converter
Type=Application
Categories=Utility;
Keywords=convert;converter;image;video;audio;document;
StartupNotify=true
Terminal=false
MimeType=image/jpeg;image/png;image/webp;image/heic;image/tiff;image/avif;video/mp4;video/quicktime;audio/mpeg;audio/flac;application/pdf;text/plain;application/vnd.openxmlformats-officedocument.wordprocessingml.document;
EOF

cat > "$AUTOSTART_DIR/citrus-converter.desktop" << EOF
[Desktop Entry]
Type=Application
Name=Citrus Converter
Comment=Background file conversion wheel
Exec=$CITRUS_EXEC --background
Terminal=false
X-GNOME-Autostart-enabled=true
NoDisplay=true
EOF

echo -e "${GREEN}✅ Desktop entry created.${NC}"
echo -e "${GREEN}✅ Citrus will start automatically in the system tray at login.${NC}"
echo ""

# Verify installation
echo -e "${BOLD}Step 5: Verifying installation...${NC}"
echo ""

citrus-cli check-deps 2>/dev/null || python3 -m citrus_converter.cli check-deps

echo ""
echo -e "${ORANGE}${BOLD}  🍊 Installation Complete!${NC}"
echo ""
echo "  Launch the app:"
echo "    • GUI:  citrus-converter"
echo "    • CLI:  citrus-cli convert photo.heic png"
echo "    • CLI:  citrus-cli --help"
echo ""
echo "  Or find 'Citrus Converter' in your application menu."
echo ""
