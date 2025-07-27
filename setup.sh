#!/bin/bash

# ==============================================================================
#  Personal AI Career Co-Pilot Project Setup Script
# ==============================================================================
#
#  This script creates the complete directory and file structure for the
#  project as specified in the SRS and our action plan.
#
#  Instructions:
#  1. Save this file as 'setup.sh' in your main project folder (e.g., 'ai-career-pilot/').
#  2. Open your terminal and navigate to that folder.
#  3. Make the script executable by running: chmod +x setup.sh
#  4. Run the script: ./setup.sh
#
# ==============================================================================

echo "🚀 Starting setup for the Personal AI Career Co-Pilot..."

# --- Create Core Directories ---
echo "-> Creating primary directories..."
mkdir -p .github/workflows
mkdir -p functions/kb
mkdir -p functions/utils
mkdir -p public
mkdir -p scripts

# --- Create Root-Level Files ---
echo "-> Creating root configuration files..."
touch .firebaserc
touch firebase.json
touch firestore.indexes.json
touch firestore.rules
touch package.json
touch storage.rules

# --- Create GitHub Actions Workflow File ---
echo "-> Creating GitHub Actions workflow file..."
touch .github/workflows/deploy.yml

# --- Create Backend 'functions' Files ---
echo "-> Creating backend files in 'functions/'..."
touch functions/config.py
touch functions/main.py
touch functions/requirements.txt
touch functions/utils/firebase_client.py
touch functions/utils/pdf_generator.py
touch functions/utils/scraper.py

# --- Create Knowledge Base Placeholder Files ---
echo "-> Creating knowledge base files in 'functions/kb/'..."
touch "functions/kb/Gold Standard Knowledge Artifact.md"
touch functions/kb/australian_sector_glossary.md
touch functions/kb/pdf_themes_json.json
touch functions/kb/skill_taxonomy_community_services.md
S
# --- Create Frontend 'public' Files ---
echo "-> Creating frontend files in 'public/'..."
touch public/api.js
touch public/app.js
touch public/index.html
touch public/manifest.json
touch public/style.css
touch public/sw.js

# --- Create 'scripts' Files ---
echo "-> Creating local script files in 'scripts/'..."
touch scripts/populate_profile.py
touch scripts/requirements.txt

echo ""
echo "✅ Project structure created successfully!"
echo "You can now populate these files with the code we have developed."
