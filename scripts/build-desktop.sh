#!/bin/bash

set -e

echo "🖥️  Building EduPilot Desktop App"
echo "================================="

cd apps/desktop

echo "Installing dependencies..."
npm install

echo "Building React app..."
npm run build

echo "Building Electron installers..."
npm run electron:build

echo ""
echo "✓ Build completed!"
echo ""
echo "Installers location: apps/desktop/dist/"
echo "  - Windows: EduPilot-Setup-{version}.exe"
echo "  - macOS: EduPilot-{version}.dmg"
echo "  - Linux: EduPilot-{version}.AppImage"
