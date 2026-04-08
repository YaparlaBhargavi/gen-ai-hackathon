@echo off
echo Initializing Git repository...
git init

echo Staging all files...
git add .

echo Committing changes...
git commit -m "Initial commit for the AI Productivity Platform"

echo Setting main branch...
git branch -M main

echo Adding remote origin...
git remote add origin https://github.com/YaparlaBhargavi/gen-ai-hackathon.git

echo Pushing to GitHub...
git push -u origin main

echo.
echo Process complete! Press any key to exit.
pause
