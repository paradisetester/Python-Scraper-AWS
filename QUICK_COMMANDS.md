# Quick Commands for Your EC2 Instance

## Instance Information
- **Name**: cars-scraper-server
- **Instance ID**: i-026bab79e30172976
- **Public IP**: 3.15.159.148
- **DNS Name**: ec2-3-15-159-148.us-east-2.compute.amazonaws.com
- **Instance Type**: t3.medium
- **Key Pair**: cars-scraper
- **Security Group**: launch-wizard-1
- **Region**: us-east-2 (Ohio)

## Quick SSH Connection
```bash
# Connect to your instance
ssh -i cars-scraper.pem ubuntu@3.15.159.148

# Or using DNS name
ssh -i cars-scraper.pem ubuntu@ec2-3-15-159-148.us-east-2.compute.amazonaws.com
```

## File Upload Commands
```bash
# Upload all deployment files
scp -i cars-scraper.pem -r ./aws_deployment ubuntu@3.15.159.148:/home/ubuntu/cars-scraper/

# Upload database.py
scp -i cars-scraper.pem ./database.py ubuntu@3.15.159.148:/home/ubuntu/cars-scraper/
```

## Quick Setup Commands (Run on EC2)
```bash
# 1. Update system
sudo apt update && sudo apt upgrade -y

# 2. Install essentials
sudo apt install -y python3 python3-pip python3-venv curl wget unzip htop

# 3. Install Chrome
wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | sudo apt-key add -
echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" | sudo tee /etc/apt/sources.list.d/google-chrome.list
sudo apt update && sudo apt install -y google-chrome-stable

# 4. Install ChromeDriver
CHROME_VERSION=$(google-chrome --version | cut -d " " -f3 | cut -d "." -f1)
wget -O /tmp/chromedriver.zip "https://chromedriver.storage.googleapis.com/LATEST_RELEASE_${CHROME_VERSION}/chromedriver_linux64.zip"
sudo unzip /tmp/chromedriver.zip -d /usr/local/bin/
sudo chmod +x /usr/local/bin/chromedriver

# 5. Setup application
sudo mkdir -p /opt/cars-scraper
sudo chown ubuntu:ubuntu /opt/cars-scraper
cd /opt/cars-scraper

# 6. Copy files
cp /home/ubuntu/cars-scraper/aws_deployment/requirements.txt .
cp /home/ubuntu/cars-scraper/aws_deployment/server_aws.py server.py
cp /home/ubuntu/cars-scraper/aws_deployment/scraper_aws.py scraper.py
cp /home/ubuntu/cars-scraper/database.py .

# 7. Setup Python environment
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
pip install psutil
```

## Service Setup Commands
```bash
# Create systemd service
sudo tee /etc/systemd/system/cars-scraper.service > /dev/null <<EOF
[Unit]
Description=Cars.com Scraper API - AWS Production
After=network.target

[Service]
Type=simple
User=ubuntu
Group=ubuntu
WorkingDirectory=/opt/cars-scraper
Environment=PATH=/opt/cars-scraper/venv/bin
ExecStart=/opt/cars-scraper/venv/bin/uvicorn server:app --host 0.0.0.0 --port 8000 --workers 1
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable cars-scraper
sudo systemctl start cars-scraper
```

## Testing Commands
```bash
# Test health endpoint
curl http://3.15.159.148:8000/health/

# Test WordPress connection
curl http://3.15.159.148:8000/wordpress-status/

# Test scraping API
curl -X POST "http://3.15.159.148:8000/scrape/" \
     -H "Content-Type: application/json" \
     -d '{
       "stock_type": "all",
       "zip_code": "60606",
       "start_page": 1,
       "end_page": 1,
       "user_email": "test@example.com"
     }'
```

## Monitoring Commands
```bash
# Check service status
sudo systemctl status cars-scraper

# View logs
sudo journalctl -u cars-scraper -f

# Check system resources
htop
free -h
df -h

# Check if port is listening
sudo netstat -tlnp | grep :8000
```

## Maintenance Commands
```bash
# Restart service
sudo systemctl restart cars-scraper

# Stop service
sudo systemctl stop cars-scraper

# Start service
sudo systemctl start cars-scraper

# View recent logs
sudo journalctl -u cars-scraper --no-pager -n 20

# Update system
sudo apt update && sudo apt upgrade -y
```

## WordPress Integration
Update your WordPress scraper form to use:
**API URL**: `http://3.15.159.148:8000`

## Security Group Ports
Make sure these ports are open in your security group (launch-wizard-1):
- SSH: 22
- HTTP: 80
- HTTPS: 443
- Custom: 8000

## Troubleshooting
```bash
# If service fails to start
sudo journalctl -u cars-scraper --no-pager -n 50

# Test Chrome manually
google-chrome --headless --no-sandbox --dump-dom https://www.google.com

# Check file permissions
ls -la /opt/cars-scraper/
sudo chown -R ubuntu:ubuntu /opt/cars-scraper

# Test Python imports
cd /opt/cars-scraper
source venv/bin/activate
python -c "import selenium, fastapi, requests; print('All packages work!')"
```