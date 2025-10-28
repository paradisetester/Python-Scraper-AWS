#!/bin/bash

# AWS EC2 Deployment Script for Cars.com Scraper
echo "🚀 Deploying Cars.com Scraper to AWS EC2..."

# Configuration
APP_DIR="/opt/cars-scraper"
SERVICE_NAME="cars-scraper"

# Stop existing service
echo "Stopping existing service..."
sudo systemctl stop $SERVICE_NAME 2>/dev/null || true

# Create application directory
sudo mkdir -p $APP_DIR
sudo chown $USER:$USER $APP_DIR

# Copy files
echo "Copying application files..."
cp requirements.txt $APP_DIR/
cp server_aws.py $APP_DIR/server.py
cp scraper_aws.py $APP_DIR/scraper.py
cp ../database.py $APP_DIR/

# Set up virtual environment
cd $APP_DIR
python3 -m venv venv
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt
pip install psutil  # For system monitoring

# Create systemd service file
echo "Creating systemd service..."
sudo tee /etc/systemd/system/$SERVICE_NAME.service > /dev/null <<EOF
[Unit]
Description=Cars.com Scraper API - AWS Optimized
After=network.target
StartLimitIntervalSec=0

[Service]
Type=simple
User=$USER
Group=$USER
WorkingDirectory=$APP_DIR
Environment=PATH=$APP_DIR/venv/bin
Environment=PYTHONPATH=$APP_DIR
ExecStart=$APP_DIR/venv/bin/uvicorn server:app --host 0.0.0.0 --port 8000 --workers 1
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

# Create log rotation
sudo tee /etc/logrotate.d/cars-scraper > /dev/null <<EOF
$APP_DIR/*.log {
    daily
    missingok
    rotate 7
    compress
    delaycompress
    notifempty
    copytruncate
}
EOF

# Set permissions
sudo chown -R $USER:$USER $APP_DIR
chmod +x $APP_DIR/venv/bin/*

# Reload systemd and start service
echo "Starting service..."
sudo systemctl daemon-reload
sudo systemctl enable $SERVICE_NAME
sudo systemctl start $SERVICE_NAME

# Wait for service to start
sleep 5

# Check service status
echo "Service status:"
sudo systemctl status $SERVICE_NAME --no-pager

# Test health endpoint
echo "Testing health endpoint..."
sleep 2
curl -f http://localhost:8000/health/ || echo "Health check failed - service may still be starting"

echo "✅ Deployment complete!"
echo "📊 Monitor logs: sudo journalctl -u $SERVICE_NAME -f"
echo "🔄 Restart service: sudo systemctl restart $SERVICE_NAME"
echo "📈 Check status: sudo systemctl status $SERVICE_NAME"