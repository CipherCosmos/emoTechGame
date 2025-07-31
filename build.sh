#!/bin/bash

# Emotech Quiz Game - Docker Build Script

echo "🚀 Building Emotech Quiz Game with Docker..."

# Clean up any existing containers and images
echo "🧹 Cleaning up existing containers..."
docker-compose down --remove-orphans

# Remove any dangling images
echo "🗑️  Removing dangling images..."
docker image prune -f

# Build the images
echo "🔨 Building Docker images..."
docker-compose build --no-cache

# Check if build was successful
if [ $? -eq 0 ]; then
    echo "✅ Build completed successfully!"
    echo ""
    echo "🎯 Next steps:"
    echo "1. Start the application: docker-compose up -d"
    echo "2. View logs: docker-compose logs -f"
    echo "3. Access the application:"
    echo "   - Frontend: http://localhost:3000"
    echo "   - Backend API: http://localhost:8001"
    echo "   - API Docs: http://localhost:8001/docs"
    echo "   - MongoDB Express: http://localhost:8081"
    echo ""
    echo "🛠️  Or use the Makefile:"
    echo "   - make prod     # Start production environment"
    echo "   - make dev      # Start development environment"
    echo "   - make logs     # View logs"
    echo "   - make clean    # Clean up everything"
else
    echo "❌ Build failed! Please check the error messages above."
    exit 1
fi 