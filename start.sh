#!/bin/bash

# Quick Start Script for 1NCE API Platform

echo "=================================================="
echo "1NCE API Platform - Quick Start"
echo "=================================================="
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.8 or higher."
    exit 1
fi

echo "✅ Python found: $(python3 --version)"
echo ""

# Install dependencies
echo "📦 Installing dependencies..."
pip3 install -r requirements.txt

if [ $? -ne 0 ]; then
    echo "❌ Failed to install dependencies"
    exit 1
fi

echo ""
echo "✅ Dependencies installed successfully!"
echo ""

# Check for credentials
if [ -z "$ONCE_USERNAME" ] || [ -z "$ONCE_PASSWORD" ]; then
    echo "⚠️  Credentials not found in environment variables"
    echo ""
    echo "You can enter them in the Streamlit interface"
    echo ""
fi

echo ""
echo "=================================================="
echo "Starting 1NCE API Platform..."
echo "=================================================="
echo ""
echo "🚀 FastAPI backend: http://localhost:8000"
echo "🎨 Streamlit UI: http://localhost:8501"
echo ""

# Start the integrated app
python3 run_full_app.py
