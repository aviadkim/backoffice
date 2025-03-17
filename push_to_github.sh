#!/bin/bash

# Script to push changes to GitHub
echo "Pushing FinAnalyzer v1.5.0 to GitHub..."

# Make sure we're in the right directory
cd /workspaces/backoffice

# Update version file
echo "1.5.0" > VERSION

# Configure git if needed
if [ -z "$(git config --get user.name)" ]; then
    read -p "Enter your git user name: " username
    git config --global user.name "$username"
fi

if [ -z "$(git config --get user.email)" ]; then
    read -p "Enter your git email: " email
    git config --global user.email "$email"
fi

# Configure repository if needed
if ! git remote | grep -q "origin"; then
    git remote add origin https://github.com/aviadkim/backoffice.git
else
    # Update the remote URL to ensure it's correct
    git remote set-url origin https://github.com/aviadkim/backoffice.git
fi

# Stage all changes
git add .

# Commit the changes
git commit -m "Release version 1.5.0 - Enhanced Securities Analysis Module"

# Push to the main branch
git push origin main

echo "Push completed!"
echo "FinAnalyzer v1.5.0 has been successfully pushed to GitHub."
echo "View your repository at: https://github.com/aviadkim/backoffice"
