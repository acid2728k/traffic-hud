#!/bin/bash

# Script to create GitHub repository
# Usage: ./create-github-repo.sh [GITHUB_TOKEN]

REPO_NAME="traffic-hud"
DESCRIPTION="TRAFFIC HUD - traffic information display system"

if [ -z "$1" ]; then
    echo "Usage: $0 <GITHUB_TOKEN>"
    echo ""
    echo "To get token:"
    echo "1. Go to https://github.com/settings/tokens"
    echo "2. Create new token (New token -> Generate new token (classic))"
    echo "3. Select permissions: repo (full access to repositories)"
    echo "4. Copy token and use it in command"
    exit 1
fi

GITHUB_TOKEN=$1

# Get GitHub username
USERNAME=$(curl -s -H "Authorization: token $GITHUB_TOKEN" https://api.github.com/user | grep -o '"login":"[^"]*' | cut -d'"' -f4)

if [ -z "$USERNAME" ]; then
    echo "Error: Failed to get user information. Check token."
    exit 1
fi

echo "Creating repository $REPO_NAME for user $USERNAME..."

# Create repository
RESPONSE=$(curl -s -w "\n%{http_code}" -X POST \
  -H "Authorization: token $GITHUB_TOKEN" \
  -H "Accept: application/vnd.github.v3+json" \
  https://api.github.com/user/repos \
  -d "{
    \"name\": \"$REPO_NAME\",
    \"description\": \"$DESCRIPTION\",
    \"private\": false
  }")

HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
BODY=$(echo "$RESPONSE" | sed '$d')

if [ "$HTTP_CODE" -eq 201 ]; then
    echo "✓ Repository created successfully!"
    echo ""
    echo "Adding remote and pushing code..."
    
    # Add remote
    git remote add origin https://github.com/$USERNAME/$REPO_NAME.git
    
    # Push code
    git branch -M main
    git push -u origin main
    
    echo ""
    echo "✓ Done! Repository available at:"
    echo "  https://github.com/$USERNAME/$REPO_NAME"
else
    echo "Error creating repository (HTTP $HTTP_CODE):"
    echo "$BODY"
    exit 1
fi

