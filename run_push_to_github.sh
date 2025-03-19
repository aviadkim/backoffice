#!/bin/bash

# Utility script to help pushing FinAnalyzer v1.6.0 to GitHub from CodeSpaces

echo "===== Preparing GitHub Push for FinAnalyzer v1.6.0 ====="

# Check if git is installed
if ! command -v git &> /dev/null; then
    echo "Error: Git is not installed. Please install git first."
    exit 1
fi

# Make sure permissions are set
chmod +x push_to_github.sh

# Make sure we're in the right directory
cd /workspaces/backoffice

# Update version number
echo "Updating version to 1.6.0..."
echo "1.6.0" > VERSION

# Update changelog
echo "# Changelog

## [1.6.0] - $(date +%Y-%m-%d)
### Added
- Enhanced Excel export with dynamic sheet generation
- Interactive financial visualizations
- Advanced budget tracking system
- Real-time performance monitoring
- Improved Hebrew language support

### Improved
- Code organization and structure
- Documentation updates
- Performance optimizations
- Error handling and logging

## [1.5.0] - 2024-02-15
### Added
- Excel export functionality with multiple sheets
- Financial visualizations (spending by category, monthly trends, income vs expenses)
- Enhanced transaction categorization
- Budget alerts system
- Performance tracking

### Improved
- Error handling and logging
- Documentation
- Code organization

## [1.4.0] - 2024-02-15
### Added
- Multi-language support (English/Hebrew)
- PDF document processing improvements
- Enhanced financial analysis

### Fixed
- Various bug fixes and performance improvements" > CHANGELOG.md

# Add all files to git staging
echo "Adding files to git staging area..."
git add .

# Show status
echo -e "\nCurrent status:"
git status

# Commit the changes
echo -e "\nCreating commit..."
git commit -m "v1.6.0: Enhanced Excel export and interactive visualizations"

# Set up git credentials if needed
if [ -z "$(git config --get user.name)" ]; then
    echo -e "\nGit username not set. Setting it up now:"
    read -p "Enter your git user name: " username
    git config --global user.name "$username"
fi

if [ -z "$(git config --get user.email)" ]; then
    echo -e "\nGit email not set. Setting it up now:"
    read -p "Enter your git email: " email
    git config --global user.email "$email"
fi

# Check if origin is configured
if ! git remote | grep -q "origin"; then
    echo -e "\nOrigin remote not found. Setting it up now:"
    read -p "Enter your GitHub repository URL (e.g., https://github.com/username/repo.git): " repo_url
    git remote add origin "$repo_url"
fi

# Push to GitHub
echo -e "\nPushing to GitHub..."
git push origin main

echo -e "\n===== Process Complete ====="
echo "FinAnalyzer v1.6.0 has been successfully pushed to GitHub!"
echo "You can continue working on it tomorrow."
echo "Have a great day!"
