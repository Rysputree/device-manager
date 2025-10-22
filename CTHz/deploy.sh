#!/bin/bash

# CTHz Device Management System - Single Device Deployment Script
# This script sets up the application for deployment on a single CTHz device

set -e

echo "🚀 CTHz Device Management System - Single Device Deployment"
echo "=========================================================="

# Check if running as root (recommended for device deployment)
if [ "$EUID" -ne 0 ]; then
    echo "⚠️  Warning: Not running as root. Some operations may require sudo."
fi

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p data logs certs
chmod 755 data logs certs

# Set up Python virtual environment
echo "🐍 Setting up Python environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi

source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Generate TLS certificates for CTHz communication
echo "🔐 Generating TLS certificates..."
if command -v openssl &> /dev/null; then
    python3 -c "
from src.cthz.certificates import cert_manager
cert_manager.ensure_certificates()
print('✅ Certificates generated successfully')
"
else
    echo "⚠️  OpenSSL not found. Please install OpenSSL to generate certificates."
    echo "   On Ubuntu/Debian: sudo apt-get install openssl"
    echo "   On CentOS/RHEL: sudo yum install openssl"
fi

# Initialize database
echo "🗄️  Initializing database..."
python3 -c "
from src.database.init_db import init_db
init_db()
print('✅ Database initialized successfully')
"

# Set up single-device mode
echo "🔧 Configuring single-device mode..."
python3 -c "
from src.cthz.single_device import single_device_service
group, station, device = single_device_service.ensure_default_entities()
print(f'✅ Single-device mode configured: {device.name}')
"

# Create systemd service file
echo "⚙️  Creating systemd service..."
cat > /etc/systemd/system/cthz-device-manager.service << 'SERVICE_EOF'
[Unit]
Description=CTHz Device Management System
After=network.target

[Service]
Type=simple
User=cthz
Group=cthz
WorkingDirectory=$(pwd)
Environment=PATH=$(pwd)/venv/bin
ExecStart=$(pwd)/venv/bin/python -m uvicorn src.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
SERVICE_EOF

# Create cthz user if it doesn't exist
if ! id "cthz" &>/dev/null; then
    echo "👤 Creating cthz user..."
    useradd -r -s /bin/false cthz
fi

# Set ownership
echo "🔒 Setting file permissions..."
chown -R cthz:cthz data logs certs
chmod 600 certs/*.key 2>/dev/null || true
chmod 644 certs/*.crt 2>/dev/null || true

# Enable and start service
echo "🚀 Starting service..."
systemctl daemon-reload
systemctl enable cthz-device-manager
systemctl start cthz-device-manager

# Check service status
echo "📊 Service status:"
systemctl status cthz-device-manager --no-pager

echo ""
echo "✅ Deployment completed successfully!"
echo ""
echo "🌐 Access the application at:"
echo "   http://localhost:8000"
echo "   https://localhost:8000 (if TLS is configured)"
echo ""
echo "📋 Next steps:"
echo "   1. Complete the first-time setup wizard"
echo "   2. Configure CTHz application to run on port 8443"
echo "   3. Test device communication"
echo ""
echo "🔧 Service management:"
echo "   sudo systemctl status cthz-device-manager"
echo "   sudo systemctl restart cthz-device-manager"
echo "   sudo systemctl stop cthz-device-manager"
echo ""
echo "📝 Logs:"
echo "   sudo journalctl -u cthz-device-manager -f"
echo "   tail -f logs/audit.log"
