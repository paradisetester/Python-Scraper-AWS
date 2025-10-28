#!/bin/bash

# AWS EC2 Monitoring Script for Cars.com Scraper
echo "🔍 Cars.com Scraper - AWS Monitoring Dashboard"
echo "=============================================="

SERVICE_NAME="cars-scraper"
APP_DIR="/opt/cars-scraper"

# Service Status
echo "📊 Service Status:"
sudo systemctl is-active $SERVICE_NAME
echo ""

# Resource Usage
echo "💻 System Resources:"
echo "CPU Usage: $(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d'%' -f1)%"
echo "Memory Usage: $(free | grep Mem | awk '{printf("%.1f%%", $3/$2 * 100.0)}')"
echo "Disk Usage: $(df -h / | awk 'NR==2{printf "%s", $5}')"
echo ""

# Process Information
echo "🔄 Process Information:"
ps aux | grep -E "(uvicorn|python.*server)" | grep -v grep
echo ""

# Recent Logs
echo "📝 Recent Logs (last 10 lines):"
sudo journalctl -u $SERVICE_NAME --no-pager -n 10
echo ""

# Log Files
echo "📁 Log Files:"
if [ -d "$APP_DIR" ]; then
    ls -la $APP_DIR/*.log 2>/dev/null || echo "No log files found"
else
    echo "Application directory not found"
fi
echo ""

# Network Status
echo "🌐 Network Status:"
netstat -tlnp | grep :8000 || echo "Port 8000 not listening"
echo ""

# Health Check
echo "🏥 Health Check:"
curl -s http://localhost:8000/health/ | python3 -m json.tool 2>/dev/null || echo "Health endpoint not responding"
echo ""

# Quick Actions Menu
echo "🛠️  Quick Actions:"
echo "1. Restart Service: sudo systemctl restart $SERVICE_NAME"
echo "2. View Live Logs: sudo journalctl -u $SERVICE_NAME -f"
echo "3. Stop Service: sudo systemctl stop $SERVICE_NAME"
echo "4. Start Service: sudo systemctl start $SERVICE_NAME"
echo "5. Check Full Status: sudo systemctl status $SERVICE_NAME"