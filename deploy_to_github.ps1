# Script to deploy to GitHub - Windows PowerShell version

# Function to print step messages
function Print-Step {
    param([string]$step, [string]$message)
    Write-Host "[STEP $step] $message" -ForegroundColor Yellow
}

# Function to print success messages
function Print-Success {
    param([string]$message)
    Write-Host "[SUCCESS] $message" -ForegroundColor Green
}

# Read the current version
$VERSION = Get-Content .\VERSION
Print-Step -step 1 -message "Current version is $VERSION"

# Create a new branch for this version
$BRANCH_NAME = "v$VERSION"
Print-Step -step 2 -message "Creating new branch $BRANCH_NAME"
git checkout -b $BRANCH_NAME

# Stage all changes
Print-Step -step 3 -message "Staging all changes"
git add .

# Commit the changes with a version message
Print-Step -step 4 -message "Committing changes"
git commit -m "גרסה $VERSION - שיפורי ביצועים וטיפול בקבצים"

# Push to GitHub
Print-Step -step 5 -message "Pushing to GitHub"
git push origin $BRANCH_NAME

Print-Success -message "Branch $BRANCH_NAME pushed to GitHub!"
Print-Success -message "עכשיו אפשר לפתוח Pull Request בגיטהאב כדי למזג את השינויים למאסטר"
Print-Success -message "כתובת: https://github.com/aviadkim/backoffice/pull/new/$BRANCH_NAME"

Write-Host ""
Write-Host "--------------------------------------------------------------"
Write-Host "כדי לחזור לענף הראשי (master) הקלד:"
Write-Host "git checkout master"
Write-Host "--------------------------------------------------------------" 