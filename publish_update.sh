#!/bin/bash

# Caption5 Developer Update Script
# This script helps developers commit and push their changes

echo "🚀 Publishing Caption5 Update..."

# Check if we're in a git repository
if [ ! -d ".git" ]; then
    echo "❌ Error: Not in a git repository. Please run this script from the caption5 directory."
    exit 1
fi

# Check current status
echo "📊 Current Git status:"
git status --short

# Check if there are changes to commit
if [ -z "$(git status --porcelain)" ]; then
    echo "✅ No changes to commit. Working directory is clean."
    exit 0
fi

echo ""
echo "📝 Changes detected. Please provide a commit message:"
echo "   (Use a descriptive message like 'Add new feature X' or 'Fix issue Y')"
echo ""

# Get commit message from user
read -p "Commit message: " commit_message

if [ -z "$commit_message" ]; then
    echo "❌ Commit message cannot be empty."
    exit 1
fi

# Stage all changes
echo "📦 Staging changes..."
git add .

# Commit changes
echo "💾 Committing changes..."
if git commit -m "$commit_message"; then
    echo "✅ Commit successful!"
    
    # Check if remote is configured
    if git remote -v | grep -q "origin"; then
        echo "🚀 Pushing to remote repository..."
        if git push origin main; then
            echo "🎉 Update published successfully!"
            echo ""
            echo "📋 Summary:"
            echo "   - Commit: $(git rev-parse --short HEAD)"
            echo "   - Message: $commit_message"
            echo "   - Pushed to: origin/main"
        else
            echo "❌ Push failed. You may need to configure your remote repository."
            echo "   Run: git remote add origin [YOUR_REPOSITORY_URL]"
        fi
    else
        echo "⚠️  No remote repository configured."
        echo "   To set up remote: git remote add origin [YOUR_REPOSITORY_URL]"
        echo "   Then run: git push -u origin main"
    fi
else
    echo "❌ Commit failed. Please check your changes and try again."
    exit 1
fi
