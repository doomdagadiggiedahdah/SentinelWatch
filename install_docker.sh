#!/bin/bash
set -e

echo "🐳 Installing Docker and Docker Compose for SentinelNet..."

# Detect OS
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    # Linux (Ubuntu/Debian)
    echo "📦 Detected Linux (Ubuntu/Debian)"
    
    # Check if already installed
    if command -v docker &> /dev/null; then
        echo "✅ Docker is already installed: $(docker --version)"
    else
        echo "📥 Installing Docker..."
        sudo apt-get update
        sudo apt-get install -y ca-certificates curl gnupg lsb-release
        
        # Add Docker's official GPG key
        sudo mkdir -p /etc/apt/keyrings
        curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
        
        # Set up Docker repository
        echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
        
        # Install Docker
        sudo apt-get update
        sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
        
        echo "✅ Docker installed successfully"
    fi
    
    # Check if docker-compose is installed
    if command -v docker-compose &> /dev/null; then
        echo "✅ Docker Compose is already installed: $(docker-compose --version)"
    else
        echo "📥 Installing Docker Compose..."
        sudo apt-get install -y docker-compose
        echo "✅ Docker Compose installed successfully"
    fi
    
    # Add user to docker group (optional, for running without sudo)
    if ! groups | grep -q docker; then
        echo "👤 Adding current user to docker group..."
        sudo usermod -aG docker "$USER"
        echo "⚠️  Please log out and log back in, or run: newgrp docker"
    fi
    
elif [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    echo "📦 Detected macOS"
    
    if command -v docker &> /dev/null; then
        echo "✅ Docker is already installed: $(docker --version)"
    else
        echo "📥 Installing Docker Desktop for macOS..."
        echo "Please download and install Docker Desktop from: https://www.docker.com/products/docker-desktop"
        echo "After installation, re-run this script to verify."
        exit 1
    fi
    
else
    echo "❌ Unsupported OS: $OSTYPE"
    echo "Please install Docker manually from https://docs.docker.com/get-docker/"
    exit 1
fi

# Verify installation
echo ""
echo "🔍 Verifying installation..."
docker --version
docker-compose --version

echo ""
echo "✅ All set! You can now run: ./docker-start.sh up"