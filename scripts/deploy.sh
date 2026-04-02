#!/bin/bash

set -e

echo "🚀 Deploying EduPilot to Production"
echo "===================================="

# Load environment variables
if [ -f .env.production ]; then
    export $(cat .env.production | xargs)
fi

# Build and push Docker images
echo "Building Docker images..."
docker-compose -f docker-compose.prod.yml build

echo "Pushing images to registry..."
docker-compose -f docker-compose.prod.yml push

# Deploy to server (example using SSH)
echo "Deploying to production server..."
ssh $DEPLOY_USER@$DEPLOY_HOST << 'ENDSSH'
    cd /opt/edupilot
    git pull origin main
    docker-compose -f docker-compose.prod.yml pull
    docker-compose -f docker-compose.prod.yml up -d
    
    # Run migrations
    docker-compose -f docker-compose.prod.yml exec -T api-gateway dotnet ef database update
    
    # Health check
    sleep 10
    curl -f http://localhost:5000/health || exit 1
ENDSSH

echo ""
echo "✓ Deployment completed successfully!"
echo ""
echo "Verifying services..."
curl -f https://api.edupilot.ai/health && echo "✓ API Gateway is healthy"
curl -f https://app.edupilot.ai && echo "✓ Web App is accessible"
curl -f https://edupilot.ai && echo "✓ Marketing Site is accessible"

echo ""
echo "🎉 Deployment successful!"
