#!/bin/bash
#
# Digital Signage Client Setup Script
# Shell wrapper that installs Python first, then runs the main Python setup
#
# Usage:
#   curl -L https://raw.githubusercontent.com/tbnobed/signage/main/setup_client.sh | bash
#   # OR
#   wget https://raw.githubusercontent.com/tbnobed/signage/main/setup_client.sh && bash setup_client.sh
#

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# GitHub repository
GITHUB_REPO="https://raw.githubusercontent.com/tbnobed/signage/main"
PYTHON_SCRIPT_URL="${GITHUB_REPO}/setup_client.py"

print_header() {
    echo -e "${BLUE}============================================================${NC}"
    echo -e "${BLUE}     Digital Signage Client Setup${NC}"
    echo -e "${BLUE}============================================================${NC}"
    echo ""
    echo "This script will prepare your system and install the signage client."
    echo ""
}

check_sudo() {
    if ! sudo -n true 2>/dev/null; then
        echo -e "${YELLOW}⚠️  This script requires sudo access for package installation.${NC}"
        echo "Please enter your password when prompted."
        sudo -v
    fi
}

detect_system() {
    if command -v apt >/dev/null 2>&1; then
        PACKAGE_MANAGER="apt"
        UPDATE_CMD="sudo apt update"
        INSTALL_CMD="sudo apt install -y"
    elif command -v yum >/dev/null 2>&1; then
        PACKAGE_MANAGER="yum"
        UPDATE_CMD=""
        INSTALL_CMD="sudo yum install -y"
    elif command -v dnf >/dev/null 2>&1; then
        PACKAGE_MANAGER="dnf"
        UPDATE_CMD=""
        INSTALL_CMD="sudo dnf install -y"
    else
        echo -e "${RED}❌ Unsupported system. This script requires apt, yum, or dnf.${NC}"
        echo "Please install Python 3, pip, and a media player manually:"
        echo "  - Python 3 and pip"
        echo "  - Media player: omxplayer (Pi), vlc, or ffmpeg"
        exit 1
    fi
    
    echo -e "${GREEN}✅ Detected package manager: ${PACKAGE_MANAGER}${NC}"
}

install_python() {
    echo -e "${BLUE}📦 Installing Python and basic dependencies...${NC}"
    
    # Update package list if needed
    if [ -n "$UPDATE_CMD" ]; then
        echo "   Updating package list..."
        $UPDATE_CMD
    fi
    
    # Install Python packages
    if [ "$PACKAGE_MANAGER" = "apt" ]; then
        $INSTALL_CMD python3 python3-pip wget curl
    elif [ "$PACKAGE_MANAGER" = "yum" ] || [ "$PACKAGE_MANAGER" = "dnf" ]; then
        $INSTALL_CMD python3 python3-pip wget curl
    fi
    
    echo -e "${GREEN}   ✅ Python 3 and pip installed${NC}"
}

check_python() {
    if command -v python3 >/dev/null 2>&1; then
        PYTHON_CMD="python3"
    elif command -v python >/dev/null 2>&1; then
        PYTHON_VERSION=$(python --version 2>&1 | cut -d' ' -f2 | cut -d'.' -f1)
        if [ "$PYTHON_VERSION" = "3" ]; then
            PYTHON_CMD="python"
        else
            return 1
        fi
    else
        return 1
    fi
    
    echo -e "${GREEN}✅ Python 3 is available${NC}"
    return 0
}

download_and_run_python_script() {
    echo -e "${BLUE}⬇️  Downloading and running Python setup script...${NC}"
    
    # Create temporary directory
    TEMP_DIR=$(mktemp -d)
    SCRIPT_PATH="${TEMP_DIR}/setup_client.py"
    
    # Download the Python script
    if command -v wget >/dev/null 2>&1; then
        wget -q -O "$SCRIPT_PATH" "$PYTHON_SCRIPT_URL"
    elif command -v curl >/dev/null 2>&1; then
        curl -s -L -o "$SCRIPT_PATH" "$PYTHON_SCRIPT_URL"
    else
        echo -e "${RED}❌ Neither wget nor curl is available${NC}"
        exit 1
    fi
    
    if [ ! -f "$SCRIPT_PATH" ]; then
        echo -e "${RED}❌ Failed to download Python setup script${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}   ✅ Downloaded setup script${NC}"
    echo ""
    
    # Run the Python script
    $PYTHON_CMD "$SCRIPT_PATH"
    
    # Clean up
    rm -rf "$TEMP_DIR"
}

main() {
    print_header
    
    # Check if Python is already available
    if check_python; then
        echo "Python 3 is already installed, skipping installation."
    else
        echo "Python 3 not found, installing..."
        check_sudo
        detect_system
        install_python
        
        # Verify installation
        if ! check_python; then
            echo -e "${RED}❌ Failed to install Python 3${NC}"
            exit 1
        fi
    fi
    
    # Download and run the main Python setup script
    download_and_run_python_script
}

# Run main function
main "$@"