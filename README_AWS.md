# AWS EC2 Deployment Guide - Cars.com Scraper

## Overview
This guide helps you deploy the Cars.com scraper on AWS EC2 for 24/7 operation with enhanced reliability and timeout prevention.

## Prerequisites
- AWS EC2 instance (recommended: t3.medium or larger)
- Ubuntu 20.04 LTS or newer
- At least 4GB RAM and 20GB storage
- Security group allowing inbound traffic on port 8000

## Quick Deployment

### 1. Launch EC2 Instance
```bash
# Recommended instance type: t3.medium
# AMI: Ubuntu Server 20.04 LTS
# Storage: 20GB GP2
# Security Group: Allow HTTP (80), HTTPS (443), Custom TCP (8000)
```

### 2. Connect and Setup
```bash
# Connect to your EC2 instance
ssh -i your-key.pem ubuntu@your-ec2-ip

# Update system
sudo apt update && sudo apt upgrade -y

# Clone or upload your scraper files
# Upload the aws_deployment folder to /home/ubuntu/
```

### 3. Run Setup Script
```bash
cd /home/ubuntu/aws_deployment
chmod +x setup_ec2.sh
./setup_ec2.sh
```

### 4. Deploy Application
```bash
chmod +x deploy.sh
./deploy.sh
```

## Manual Setup (Alternative)

### 1. Install Dependencies
```bash
# Install Python and Chrome
sudo apt update
sudo apt install python3 python3-pip python3-venv -y

# Install Chrome
wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | sudo apt-key add -
echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" | sudo tee /etc/apt/sources.list.d/google-chrome.list
sudo apt update
sudo apt install google-chrome-stable -y

# Install ChromeDriver
CHROME_VERSION=$(google-chrome --version | cut -d " " -f3 | cut -d "." -f1)
wget -O /tmp/chromedriver.zip "https://chromedriver.storage.googleapis.com/LATEST_RELEASE_${CHROME_VERSION}/chromedriver_linux64.zip"
sudo unzip /tmp/chromedriver.zip -d /usr/local/bin/
sudo chmod +x /usr/local/bin/chromedriver
```

### 2. Setup Application
```bash
# Create app directory
sudo mkdir -p /opt/cars-scraper
sudo chown $USER:$USER /opt/cars-scraper
cd /opt/cars-scraper

# Copy files
cp ~/aws_deployment/requirements.txt .
cp ~/aws_deployment/server_aws.py server.py
cp ~/aws_deployment/scraper_aws.py scraper.py
cp ~/aws_deployment/../database.py .

# Setup virtual environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install psutil
```

### 3. Create System Service
```bash
sudo tee /etc/systemd/system/cars-scraper.service > /dev/null <<EOF
[Unit]
Description=Cars.com Scraper API - AWS
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=/opt/cars-scraper
Environment=PATH=/opt/cars-scraper/venv/bin
ExecStart=/opt/cars-scraper/venv/bin/uvicorn server:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable cars-scraper
sudo systemctl start cars-scraper
```

## Monitoring and Management

### Check Service Status
```bash
# Quick monitoring
./monitoring.sh

# Service status
sudo systemctl status cars-scraper

# Live logs
sudo journalctl -u cars-scraper -f

# Health check
curl http://localhost:8000/health/
```

### Common Commands
```bash
# Restart service
sudo systemctl restart cars-scraper

# Stop service
sudo systemctl stop cars-scraper

# Start service
sudo systemctl start cars-scraper

# View logs
sudo journalctl -u cars-scraper --no-pager -n 50
```

## AWS-Specific Optimizations

### 1. Enhanced Error Handling
- Progressive retry logic with exponential backoff
- Better timeout management for network requests
- Improved WebDriver stability

### 2. Resource Management
- Reduced concurrent workers (2-3 vs 6)
- Smaller batch sizes (50 vs 100)
- Memory-optimized Chrome options
- Automatic driver cleanup

### 3. Monitoring
- System resource tracking
- Health check endpoints
- Structured logging
- Automatic service restart

## Security Group Configuration

### Inbound Rules
```
Type: HTTP
Protocol: TCP
Port: 80
Source: 0.0.0.0/0

Type: HTTPS  
Protocol: TCP
Port: 443
Source: 0.0.0.0/0

Type: Custom TCP
Protocol: TCP
Port: 8000
Source: 0.0.0.0/0 (or restrict to your IP)

Type: SSH
Protocol: TCP
Port: 22
Source: Your IP
```

## Troubleshooting

### Service Won't Start
```bash
# Check logs
sudo journalctl -u cars-scraper --no-pager -n 20

# Check Chrome installation
google-chrome --version
chromedriver --version

# Test manually
cd /opt/cars-scraper
source venv/bin/activate
python server.py
```

### High Memory Usage
```bash
# Monitor resources
htop
free -h
df -h

# Restart service
sudo systemctl restart cars-scraper
```

### Chrome Issues
```bash
# Reinstall Chrome
sudo apt remove google-chrome-stable
sudo apt install google-chrome-stable

# Update ChromeDriver
sudo rm /usr/local/bin/chromedriver
# Re-run ChromeDriver installation from setup script
```

## Performance Tuning

### For t3.medium (4GB RAM)
- max_workers: 2
- batch_size: 50
- page_load_timeout: 45s

### For t3.large (8GB RAM)
- max_workers: 3
- batch_size: 75
- page_load_timeout: 30s

## Backup and Recovery

### Backup Configuration
```bash
# Backup service file
sudo cp /etc/systemd/system/cars-scraper.service ~/cars-scraper.service.backup

# Backup application
tar -czf ~/cars-scraper-backup.tar.gz /opt/cars-scraper
```

### Recovery
```bash
# Restore from backup
sudo tar -xzf ~/cars-scraper-backup.tar.gz -C /

# Reload and restart
sudo systemctl daemon-reload
sudo systemctl restart cars-scraper
```

## Cost Optimization

### Instance Scheduling
```bash
# Stop instance during low usage (optional)
# Use AWS Lambda or CloudWatch Events to start/stop EC2

# Example: Stop at night, start in morning
# 0 22 * * * aws ec2 stop-instances --instance-ids i-1234567890abcdef0
# 0 6 * * * aws ec2 start-instances --instance-ids i-1234567890abcdef0
```

## Support

For issues or questions:
1. Check logs: `sudo journalctl -u cars-scraper -f`
2. Run monitoring: `./monitoring.sh`
3. Test health: `curl http://localhost:8000/health/`
4. Check system resources: `htop` and `free -h`