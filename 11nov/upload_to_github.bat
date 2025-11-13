@echo off
echo Uploading Smart Music project to GitHub...

echo Adding all files to git...
git add .

echo Committing changes...
git commit -m "Initial commit: Complete Smart Music AI platform with gesture recognition, multiple recommendation systems, and Spotify integration"

echo Setting main branch...
git branch -M main

echo Pushing to GitHub...
git push -u origin main

echo Upload complete!
pause
