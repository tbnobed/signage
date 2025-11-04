#!/bin/bash
# DisplayHQ VNC Installation Script
# Installs and configures x11vnc for remote desktop access to digital signage displays
# 
# Usage:
#   curl -sSL https://raw.githubusercontent.com/tbnobed/signage/main/install_vnc.sh | bash
#   OR download and run manually:
#   wget https://raw.githubusercontent.com/tbnobed/signage/main/install_vnc.sh
#   chmod +x install_vnc.sh
#   ./install_vnc.sh

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}   DisplayHQ VNC Server Installation${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Check if running as root
if [ "$EUID" -eq 0 ]; then 
    echo -e "${RED}❌ Do not run this script as root/sudo${NC}"
    echo -e "${YELLOW}   Run as regular user: ./install_vnc.sh${NC}"
    exit 1
fi

# Get username
CURRENT_USER=$(whoami)
echo -e "${GREEN}👤 Installing VNC for user: ${CURRENT_USER}${NC}"
echo ""

# Install x11vnc and expect
echo -e "${BLUE}📦 Installing required packages...${NC}"
sudo apt update
sudo apt install -y x11vnc expect

if ! command -v x11vnc &> /dev/null; then
    echo -e "${RED}❌ x11vnc installation failed${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Packages installed successfully${NC}"
echo ""

# Create VNC password directory
VNC_DIR="$HOME/.vnc"
mkdir -p "$VNC_DIR"

# Set VNC password
echo -e "${BLUE}🔐 Setting VNC password...${NC}"
echo -e "${YELLOW}   Setting default password: TBN@dmin!!${NC}"

# Create temporary expect script
EXPECT_SCRIPT=$(mktemp)
cat > "$EXPECT_SCRIPT" <<'EXPECTEOF'
#!/usr/bin/expect -f
set timeout 10
set password "TBN@dmin!!"
set passwd_file [lindex $argv 0]

spawn x11vnc -storepasswd $passwd_file
expect {
    "Enter VNC password:" {
        send "$password\r"
        expect "Verify password:" {
            send "$password\r"
        }
    }
    timeout {
        exit 1
    }
}
expect eof
EXPECTEOF

chmod +x "$EXPECT_SCRIPT"

# Run expect script
if "$EXPECT_SCRIPT" "$VNC_DIR/passwd" >/dev/null 2>&1; then
    echo -e "   ✅ Password set via expect"
else
    # Fallback: try direct write (less secure but works)
    echo -e "   ⚠️  Expect method failed, using fallback"
    # VNC password uses a simple obfuscation - we'll use x11vnc's built-in method differently
    echo -e "TBN@dmin!!\nTBN@dmin!!" | script -q -c "x11vnc -storepasswd $VNC_DIR/passwd" /dev/null >/dev/null 2>&1
fi

# Cleanup temp file
rm -f "$EXPECT_SCRIPT"

# Verify password file was created
if [ ! -f "$VNC_DIR/passwd" ]; then
    echo -e "${RED}❌ Failed to create VNC password file${NC}"
    echo -e "${YELLOW}   Please run manually after installation:${NC}"
    echo -e "${YELLOW}   x11vnc -storepasswd ~/.vnc/passwd${NC}"
    echo -e "${YELLOW}   sudo systemctl restart x11vnc${NC}"
    echo -e "${YELLOW}   (Continuing with installation anyway...)${NC}"
    # Create empty file so service can still be created
    touch "$VNC_DIR/passwd"
fi

chmod 600 "$VNC_DIR/passwd"
echo -e "${GREEN}✅ VNC password configured${NC}"
echo ""

# Create systemd service for x11vnc
echo -e "${BLUE}⚙️  Creating systemd service...${NC}"

SERVICE_FILE="/etc/systemd/system/x11vnc.service"
sudo tee "$SERVICE_FILE" > /dev/null <<EOF
[Unit]
Description=x11vnc VNC Server for DisplayHQ
After=display-manager.service network.target

[Service]
Type=simple
User=$CURRENT_USER
Environment=DISPLAY=:0
Environment=XAUTHORITY=/home/$CURRENT_USER/.Xauthority
ExecStart=/usr/bin/x11vnc -display :0 -auth /home/$CURRENT_USER/.Xauthority -forever -loop -noxdamage -repeat -rfbauth /home/$CURRENT_USER/.vnc/passwd -rfbport 5900 -shared
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

if [ ! -f "$SERVICE_FILE" ]; then
    echo -e "${RED}❌ Failed to create systemd service${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Systemd service created${NC}"

# Reload systemd and enable service
echo -e "${BLUE}🔄 Enabling VNC service...${NC}"
sudo systemctl daemon-reload
sudo systemctl enable x11vnc.service
sudo systemctl start x11vnc.service

# Check service status
sleep 2
if systemctl is-active --quiet x11vnc.service; then
    echo -e "${GREEN}✅ VNC server is running${NC}"
else
    echo -e "${RED}⚠️  VNC server may not be running yet (will start after reboot)${NC}"
fi

echo ""

# Get IP address
IP_ADDRESS=$(hostname -I | awk '{print $1}')

# Display completion message
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}   ✅ VNC Installation Complete!${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "${BLUE}Connection Details:${NC}"
echo -e "  IP Address:   ${YELLOW}${IP_ADDRESS}${NC}"
echo -e "  VNC Port:     ${YELLOW}5900${NC}"
echo -e "  Full Address: ${YELLOW}${IP_ADDRESS}:5900${NC}"
echo -e "  Password:     ${YELLOW}TBN@dmin!!${NC}"
echo ""
echo -e "${BLUE}VNC Clients:${NC}"
echo -e "  • Windows/Mac/Linux: RealVNC Viewer (https://www.realvnc.com/en/connect/download/viewer/)"
echo -e "  • Windows: TightVNC Viewer (https://www.tightvnc.com/)"
echo -e "  • macOS: Built-in Screen Sharing (vnc://${IP_ADDRESS}:5900)"
echo ""
echo -e "${BLUE}Service Management:${NC}"
echo -e "  Stop VNC:    ${YELLOW}sudo systemctl stop x11vnc${NC}"
echo -e "  Start VNC:   ${YELLOW}sudo systemctl start x11vnc${NC}"
echo -e "  Restart VNC: ${YELLOW}sudo systemctl restart x11vnc${NC}"
echo -e "  Status:      ${YELLOW}sudo systemctl status x11vnc${NC}"
echo -e "  Disable:     ${YELLOW}sudo systemctl disable x11vnc${NC}"
echo ""
echo -e "${BLUE}Change Password:${NC}"
echo -e "  ${YELLOW}x11vnc -storepasswd ~/.vnc/passwd${NC}"
echo -e "  ${YELLOW}sudo systemctl restart x11vnc${NC}"
echo ""
echo -e "${BLUE}Firewall:${NC}"
echo -e "  If you can't connect, allow port 5900:"
echo -e "  ${YELLOW}sudo ufw allow 5900/tcp${NC}"
echo ""
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
