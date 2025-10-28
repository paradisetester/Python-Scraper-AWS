# Complete AWS EC2 Setup Guide - Cars.com Scraper

## Step 1: Launch EC2 Instance

### 1.1 AWS Console Setup
1. Login to AWS Console → EC2 Dashboard
2. Click "Launch Instance"
3. **Name**: `cars-scraper-server`
4. **AMI**: Ubuntu Server 22.04 LTS (Free tier eligible)
5. **Instance Type**: `t3.medium` (4GB RAM, 2 vCPUs)
6. **Key Pair**: Create new or select existing `.pem` file
7. **Storage**: 20GB gp3 (General Purpose SSD)

### 1.2 Security Group Configuration
Create new security group with these rules:

**Inbound Rules:**
```
SSH          | TCP | 22   | Your IP Address
HTTP         | TCP | 80   | 0.0.0.0/0
HTTPS        | TCP | 443  | 0.0.0.0/0
Custom TCP   | TCP | 8000 | 0.0.0.0/0
```

**Outbound Rules:**
```
All Traffic  | All | All  | 0.0.0.0/0
```

### 1.3 Launch Instance
- Review settings and click "Launch Instance"
- Wait for instance to reach "Running" state
- Note down the **Public IPv4 address**  (3.15.159.148)

## Step 2: Connect to EC2 Instance

### 2.1 SSH Connection
```bash
# Make key file secure (Windows users: skip this)
chmod 400 cars-scraper.pem

# Connect to your specific instance
ssh -i cars-scraper.pem ubuntu@3.15.159.148

# Alternative using DNS name:
ssh -i cars-scraper.pem ubuntu@ec2-3-15-159-148.us-east-2.compute.amazonaws.com
```

### 2.2 Initial System Update
```bash
# Update package lists
sudo apt update && sudo apt upgrade -y

# Install essential tools
sudo apt install -y curl wget unzip htop git
```

## Step 3: Upload Scraper Files

### 3.1 Create Project Directory
```bash
# Create directory for scraper files
mkdir -p /home/ubuntu/cars-scraper
cd /home/ubuntu/cars-scraper
```

### 3.2 Upload Files (Choose One Method)

**Method A: Using SCP (from your local machine)**
```bash
# Upload entire aws_deployment folder
scp -i cars-scraper.pem -r ./aws_deployment ubuntu@3.15.159.148:/home/ubuntu/cars-scraper/

# Upload individual files
scp -i cars-scraper.pem ./database.py ubuntu@3.15.159.148:/home/ubuntu/cars-scraper/
```

**Method B: Using Git (if you have a repository)**
```bash
# Clone your repository
git clone https://github.com/yourusername/cars-scraper.git
cd cars-scraper/api/Python_Script/aws_deployment
```

**Method C: Manual File Creation (copy-paste content)**
```bash
# Create each file manually and paste content
nano requirements.txt
nano server_aws.py
nano scraper_aws.py
nano database.py
nano setup_ec2.sh
nano deploy.sh
nano monitoring.sh
```

## Step 4: Install Dependencies

### 4.1 Install Python and Chrome
```bash
# Install Python 3 and pip
sudo apt install -y python3 python3-pip python3-venv

# Add Google Chrome repository
wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | sudo apt-key add -
echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" | sudo tee /etc/apt/sources.list.d/google-chrome.list

# Update and install Chrome
sudo apt update
sudo apt install -y google-chrome-stable

# Verify Chrome installation
google-chrome --version
```

### 4.2 Install ChromeDriver
```bash
# Get Chrome version and install matching ChromeDriver
CHROME_VERSION=$(google-chrome --version | cut -d " " -f3 | cut -d "." -f1)
echo "Chrome version: $CHROME_VERSION"

# Download and install ChromeDriver
wget -O /tmp/chromedriver.zip "https://chromedriver.storage.googleapis.com/LATEST_RELEASE_${CHROME_VERSION}/chromedriver_linux64.zip"
sudo unzip /tmp/chromedriver.zip -d /usr/local/bin/
sudo chmod +x /usr/local/bin/chromedriver

# Verify ChromeDriver installation
chromedriver --version
```

## Step 5: Setup Application

### 5.1 Create Application Directory
```bash
# Create app directory
sudo mkdir -p /opt/cars-scraper
sudo chown ubuntu:ubuntu /opt/cars-scraper
cd /opt/cars-scraper
```

### 5.2 Copy Files and Setup Environment
```bash
# Copy files from upload directory
cp /home/ubuntu/cars-scraper/aws_deployment/requirements.txt .
cp /home/ubuntu/cars-scraper/aws_deployment/server_aws.py server.py
cp /home/ubuntu/cars-scraper/aws_deployment/scraper_aws.py scraper.py
cp /home/ubuntu/cars-scraper/database.py .

# Create Python virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
pip install --upgrade pip
pip install -r requirements.txt
pip install psutil  # For system monitoring
```

### 5.3 Test Installation
```bash
# Test if everything works
python -c "import selenium, fastapi, requests; print('All packages installed successfully')"

# Test Chrome and ChromeDriver
google-chrome --headless --no-sandbox --dump-dom https://www.google.com > /dev/null && echo "Chrome works!"
```

## Step 6: Create System Service

### 6.1 Create Service File
```bash
sudo tee /etc/systemd/system/cars-scraper.service > /dev/null <<EOF
[Unit]
Description=Cars.com Scraper API - AWS Production
After=network.target
StartLimitIntervalSec=0

[Service]
Type=simple
User=ubuntu
Group=ubuntu
WorkingDirectory=/opt/cars-scraper
Environment=PATH=/opt/cars-scraper/venv/bin
Environment=PYTHONPATH=/opt/cars-scraper
ExecStart=/opt/cars-scraper/venv/bin/uvicorn server:app --host 0.0.0.0 --port 8000 --workers 1
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
TimeoutStartSec=60
TimeoutStopSec=30

# Resource limits
LimitNOFILE=65536
LimitNPROC=4096

[Install]
WantedBy=multi-user.target
EOF
```

### 6.2 Enable and Start Service
```bash
# Reload systemd configuration
sudo systemctl daemon-reload

# Enable service to start on boot
sudo systemctl enable cars-scraper

# Start the service
sudo systemctl start cars-scraper

# Check service status
sudo systemctl status cars-scraper
```

## Step 7: Verify Installation

### 7.1 Check Service Status
```bash
# Check if service is running
sudo systemctl is-active cars-scraper

# View recent logs
sudo journalctl -u cars-scraper --no-pager -n 20

# Follow live logs
sudo journalctl -u cars-scraper -f
```

### 7.2 Test API Endpoints
```bash
# Test health endpoint locally
curl http://localhost:8000/health/

# Test from external using your EC2 public IP
curl http://3.15.159.148:8000/health/

# Expected response:
# {"status":"healthy","service":"Cars.com Scraper API - AWS","version":"2.0.0",...}
```

### 7.3 Test WordPress Connection
```bash
curl http://3.15.159.148:8000/wordpress-status/
```

## Step 8: Configure Log Rotation

### 8.1 Setup Log Rotation
```bash
sudo tee /etc/logrotate.d/cars-scraper > /dev/null <<EOF
/opt/cars-scraper/*.log {
    daily
    missingok
    rotate 7
    compress
    delaycompress
    notifempty
    copytruncate
}
EOF
```

## Step 9: Create Monitoring Script

### 9.1 Create Monitoring Dashboard
```bash
# Copy monitoring script
cp /home/ubuntu/cars-scraper/aws_deployment/monitoring.sh /opt/cars-scraper/
chmod +x /opt/cars-scraper/monitoring.sh

# Test monitoring
cd /opt/cars-scraper
./monitoring.sh
```

## Step 10: Final Configuration

### 10.1 Update WordPress URL (if needed)
```bash
# Edit scraper.py to update WordPress URL
nano /opt/cars-scraper/scraper.py

# Find and update this line:
# WORDPRESS_URL = "https://your-wordpress-site.com"

# Restart service after changes
sudo systemctl restart cars-scraper
```

### 10.2 Set File Permissions
```bash
# Ensure correct ownership
sudo chown -R ubuntu:ubuntu /opt/cars-scraper

# Set executable permissions
chmod +x /opt/cars-scraper/venv/bin/*
```

## Step 11: Test Complete Setup

### 11.1 Test Scraping API
```bash
# Test scrape endpoint with minimal parameters
curl -X POST "http://3.15.159.148:8000/scrape/" \
     -H "Content-Type: application/json" \
     -d '{
       "stock_type": "all",
       "zip_code": "60606",
       "start_page": 1,
       "end_page": 1,
       "user_email": "test@example.com"
     }'

# Expected response:
# {"message":"Scraping started successfully on AWS...","task_id":"..."}
```

### 11.2 Monitor Scraping Process
```bash
# Watch logs in real-time
sudo journalctl -u cars-scraper -f

# Check system resources
htop

# Check service status
./monitoring.sh
```

## Troubleshooting Common Issues

### Issue 1: Service Won't Start
```bash
# Check detailed logs
sudo journalctl -u cars-scraper --no-pager -n 50

# Check if port is in use
sudo netstat -tlnp | grep :8000

# Test manual start
cd /opt/cars-scraper
source venv/bin/activate
python server.py
```

### Issue 2: Chrome/ChromeDriver Issues
```bash
# Check Chrome installation
google-chrome --version
chromedriver --version

# Test Chrome headless mode
google-chrome --headless --no-sandbox --dump-dom https://www.google.com

# Reinstall if needed
sudo apt remove google-chrome-stable
sudo apt install google-chrome-stable
```

### Issue 3: Permission Issues
```bash
# Fix ownership
sudo chown -R ubuntu:ubuntu /opt/cars-scraper

# Fix permissions
chmod -R 755 /opt/cars-scraper
```

### Issue 4: Memory Issues
```bash
# Check memory usage
free -h
htop

# Restart service to free memory
sudo systemctl restart cars-scraper
```

## Maintenance Commands

### Daily Operations
```bash
# Check service status
sudo systemctl status cars-scraper

# View recent logs
sudo journalctl -u cars-scraper --no-pager -n 20

# Monitor resources
./monitoring.sh

# Restart if needed
sudo systemctl restart cars-scraper
```

### Weekly Maintenance
```bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Clean up logs
sudo journalctl --vacuum-time=7d

# Check disk space
df -h
```

## Security Considerations

### 11.1 Firewall Setup (Optional)
```bash
# Enable UFW firewall
sudo ufw enable

# Allow SSH, HTTP, HTTPS, and custom port
sudo ufw allow 22
sudo ufw allow 80
sudo ufw allow 443
sudo ufw allow 8000

# Check firewall status
sudo ufw status
```

### 11.2 Regular Updates
```bash
# Set up automatic security updates
sudo apt install unattended-upgrades
sudo dpkg-reconfigure -plow unattended-upgrades
```

## Success Checklist

- [ ] EC2 instance launched and accessible via SSH
- [ ] Chrome and ChromeDriver installed and working
- [ ] Python environment set up with all dependencies
- [ ] Service created and running automatically
- [ ] API endpoints responding correctly
- [ ] WordPress connection working
- [ ] Monitoring script functional
- [ ] Logs being generated and rotated
- [ ] Test scraping request successful

## Next Steps

1. **Update WordPress form** to use your EC2 public IP: `http://3.15.159.148:8000`
2. **Set up domain name** (optional) and SSL certificate
3. **Configure CloudWatch** for advanced monitoring
4. **Set up automated backups** of your configuration
5. **Test email notifications** end-to-end

Your Cars.com scraper is now running 24/7 on AWS EC2 with enhanced reliability and timeout prevention!