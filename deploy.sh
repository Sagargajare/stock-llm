#!/bin/bash

# Build frontend
echo "Building frontend..."
cd frontend
npm install
npm run build

# Create static directory if it doesn't exist
cd ..
mkdir -p static

# Copy frontend build to static directory
echo "Copying frontend build to static directory..."
cp -r frontend/dist/* static/

# Commit changes
echo "Committing changes..."
git add .
git commit -m "Update static files for deployment"

# Deploy to Heroku
echo "Deploying to Heroku..."
git push heroku main

echo "Deployment complete!" 