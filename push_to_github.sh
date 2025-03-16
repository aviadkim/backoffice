#!/bin/bash

# Script to push changes to GitHub
echo "Pushing FinAnalyzer v1.3.0 to GitHub..."

# Make sure we're in the right directory
cd /workspaces/backoffice

# Update version file
echo "1.3.0" > VERSION

# Configure git if needed
if [ -z "$(git config --get user.name)" ]; then
    read -p "Enter your git user name: " username
    git config --global user.name "$username"
fi

if [ -z "$(git config --get user.email)" ]; then
    read -p "Enter your git email: " email
    git config --global user.email "$email"
fi

# Stage all changes
git add .

# Commit the changes
git commit -m "Release version 1.3.0 - Enhanced PDF Processing Module"

# Push to the main branch
git push origin main

echo "Push completed!"
echo "FinAnalyzer v1.3.0 has been successfully pushed to GitHub."
