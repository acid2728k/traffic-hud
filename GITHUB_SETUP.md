# GitHub Repository Setup Guide

## Method 1: Using Script (Recommended)

1. Get GitHub Personal Access Token:
   - Go to https://github.com/settings/tokens
   - Click "Generate new token" -> "Generate new token (classic)"
   - Select permissions: `repo` (full access to repositories)
   - Copy the token

2. Run the script:
   ```bash
   ./create-github-repo.sh YOUR_GITHUB_TOKEN
   ```

## Method 2: Via GitHub Web Interface

1. Go to https://github.com/new
2. Fill in the form:
   - **Repository name**: `traffic-hud`
   - **Description**: `TRAFFIC HUD - real-time traffic counting and analysis system with HUD interface`
   - **Visibility**: Public (or Private, your choice)
   - **DO NOT** create README, .gitignore or license (they already exist)
3. Click "Create repository"

4. After creating repository, run commands:
   ```bash
   git remote add origin https://github.com/YOUR_USERNAME/traffic-hud.git
   git branch -M main
   git push -u origin main
   ```

## Method 3: Using GitHub CLI

1. Install GitHub CLI:
   ```bash
   # macOS (via Homebrew)
   brew install gh
   
   # Or download from https://cli.github.com/
   ```

2. Authenticate:
   ```bash
   gh auth login
   ```

3. Create repository:
   ```bash
   gh repo create traffic-hud --public --description "TRAFFIC HUD - real-time traffic counting and analysis system with HUD interface" --source=. --remote=origin --push
   ```
