#!/bin/bash

# AWS EC2 Setup Script for Cars.com Scraper
echo "Setting up Cars.com Scraper on AWS EC2..."

# Update system
sudo apt update && sudo apt upgrade -y

# Install Python and pip
sudo apt install python3 python3-pip python3-venv -y

# Install Chrome and ChromeDriver
wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | sudo apt-key add -
echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" | sudo tee /etc/apt/sources.list.d/google-chrome.list
sudo apt update
sudo apt install google-chrome-stable -y

# Install ChromeDriver
CHROME_VERSION=$(google-chrome --version | cut -d " " -f3 | cut -d "." -f1)
wget -O /tmp/chromedriver.zip "https://chromedriver.storage.googleapis.com/LATEST_RELEASE_${CHROME_VERSION}/chromedriver_linux64.zip"
sudo unzip /tmp/chromedriver.zip -d /usr/local/bin/
sudo chmod +x /usr/local/bin/chromedriver

# Create application directory
sudo mkdir -p /opt/cars-scraper
sudo chown $USER:$USER /opt/cars-scraper
cd /opt/cars-scraper

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Create systemd service
sudo tee /etc/systemd/system/cars-scraper.service > /dev/null <<EOF
[Unit]
Description=Cars.com Scraper API
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=/opt/cars-scraper
Environment=PATH=/opt/cars-scraper/venv/bin
ExecStart=/opt/cars-scraper/venv/bin/uvicorn server:app --host 0.0.0.0 --port 8000 --workers 1
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable cars-scraper
sudo systemctl start cars-scraper

echo "Setup complete! Service status:"
sudo systemctl status cars-scraper