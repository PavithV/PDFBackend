#!/bin/bash

# Build script for Render deployment
echo "Starting build process..."

# Upgrade pip first
pip install --upgrade pip

# Install packages one by one to identify issues
echo "Installing Flask..."
pip install Flask==2.3.3

echo "Installing Werkzeug..."
pip install Werkzeug==2.3.7

echo "Installing PyPDF2..."
pip install PyPDF2==3.0.1

echo "Installing gunicorn..."
pip install gunicorn==21.2.0

echo "Installing flask-cors..."
pip install flask-cors==4.0.0

echo "Installing Pillow..."
pip install Pillow==9.4.0

echo "Installing pikepdf..."
pip install pikepdf==8.6.0

echo "Installing PyMuPDF..."
pip install PyMuPDF==1.20.2

echo "Build completed successfully!"
