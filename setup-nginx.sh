#!/bin/bash
set -e

# Get domain from argument or use default
DOMAIN="${1:-sentinelwatch.xyz}"

echo "🔧 Setting up Nginx for SentinelNet..."
echo "📍 Domain: $DOMAIN"

# Create nginx configuration
sudo tee /etc/nginx/sites-available/sentinelwatch > /dev/null << EOF
server {
    listen 80;
    server_name $DOMAIN www.$DOMAIN;

    location / {
        proxy_pass http://localhost:3165;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_cache_bypass \$http_upgrade;
    }

    location /api/ {
        proxy_pass http://localhost:8000/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_cache_bypass \$http_upgrade;
    }
}
EOF

# Enable site
sudo ln -sf /etc/nginx/sites-available/sentinelwatch /etc/nginx/sites-enabled/sentinelwatch
sudo rm -f /etc/nginx/sites-enabled/default

# Test configuration
echo "🧪 Testing Nginx configuration..."
sudo nginx -t

# Restart nginx
echo "🔄 Restarting Nginx..."
sudo systemctl restart nginx

echo ""
echo "✅ Nginx configured successfully!"
echo "📍 Access your site at: http://$DOMAIN"
echo ""
echo "🔐 For HTTPS/SSL (optional):"
echo "   sudo apt-get install -y certbot python3-certbot-nginx"
echo "   sudo certbot --nginx -d $DOMAIN -d www.$DOMAIN"