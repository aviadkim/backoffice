#!/bin/bash

# Colors for terminal output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print step messages
print_step() {
    echo -e "${YELLOW}[STEP $1]${NC} $2"
}

# Function to print success messages
print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

# Read the current version
VERSION=$(cat VERSION)
print_step 1 "Current version is $VERSION"

# Create a new branch for this version
BRANCH_NAME="v$VERSION"
print_step 2 "Creating new branch $BRANCH_NAME"
git checkout -b $BRANCH_NAME

# Stage all changes
print_step 3 "Staging all changes"
git add .

# Commit the changes with a version message
print_step 4 "Committing changes"
git commit -m "גרסה $VERSION - שיפורי ביצועים וטיפול בקבצים"

# Push to GitHub
print_step 5 "Pushing to GitHub"
git push origin $BRANCH_NAME

print_success "Branch $BRANCH_NAME pushed to GitHub!"
print_success "עכשיו אפשר לפתוח Pull Request בגיטהאב כדי למזג את השינויים למאסטר"
print_success "כתובת: https://github.com/aviadkim/backoffice/pull/new/$BRANCH_NAME"

echo ""
echo "--------------------------------------------------------------"
echo "כדי לחזור לענף הראשי (master) הקלד:"
echo "git checkout master"
echo "--------------------------------------------------------------" 