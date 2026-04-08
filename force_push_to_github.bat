@echo off
echo Staging all files...
git add .

echo Committing changes...
git commit -m "Add all project files"

echo Updating branch to main...
git branch -M main

echo Setting remote origin (ignoring if it already exists)...
git remote add origin https://github.com/YaparlaBhargavi/gen-ai-hackathon.git 2>nul
git remote set-url origin https://github.com/YaparlaBhargavi/gen-ai-hackathon.git

echo Force pushing to GitHub to overwrite the default README...
git push -u origin main --force

echo.
echo Process complete! Press any key to exit.
pause
