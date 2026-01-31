#!/bin/bash
# Script to incrementally push large repo to GitHub to avoid 2GB limit (Fixed for initial commit)

echo "Resetting root commit (keeping files)..."
# Remove the commit object but keep files in working directory
git update-ref -d HEAD
# Unstage all files so we can add them one by one
git rm --cached -r . > /dev/null 2>&1

echo "Step 1: Pushing core code..."
git add .gitignore *.py *.txt *.md templates/ static/ *.sh
git commit -m "Add core application code"
git push -u origin main

echo "Step 2: Pushing Haldi photos..."
git add gallery/haldi/
git commit -m "Add Haldi photos"
git push -u origin main

echo "Step 3: Pushing Ring photos..."
git add gallery/ring/
git commit -m "Add Ring photos"
git push -u origin main

echo "Step 4: Pushing Rituals photos..."
git add gallery/rituals/
git commit -m "Add Rituals photos"
git push -u origin main

echo "Step 5: Pushing Wedding photos..."
git add gallery/wedding/
git commit -m "Add Wedding photos"
git push -u origin main

echo "Step 6: Pushing remaining gallery files..."
git add gallery/
git commit -m "Add remaining gallery assets"
git push -u origin main

echo "✅ All done! Check your repo at: https://github.com/Vishesh-Paliwal/photo-categoriser"
