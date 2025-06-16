#!/bin/bash

# Build frontend
echo "Building frontend..."
cd frontend
npm install
npm run build

# The frontend build is now automatically placed in the static directory
# No need to manually copy files

# Commit changes
echo "Committing changes..."
cd ..
git add .
git commit -m "Update static files for deployment"

# Force push to Heroku (since we're serving frontend from backend)
echo "Deploying to Heroku..."
git push heroku main --force

echo "Deployment complete!" 