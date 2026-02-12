# ========================================
#   GodWeb - Deploy to Heroku (PowerShell)
# ========================================

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   GodWeb - Deploy to Heroku" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Change to script directory
Set-Location $PSScriptRoot

# Step 1: Add all changes
Write-Host "[1/4] Adding all changes to git..." -ForegroundColor Yellow
git add -A

# Step 2: Commit
Write-Host ""
$commitMsg = Read-Host "Enter commit message (or press Enter for default)"
if ([string]::IsNullOrWhiteSpace($commitMsg)) {
    $commitMsg = "Update GodWeb"
}

Write-Host ""
Write-Host "[2/4] Committing changes..." -ForegroundColor Yellow
git commit -m $commitMsg

# Step 3: Push to Heroku
Write-Host ""
Write-Host "[3/4] Pushing to Heroku..." -ForegroundColor Yellow
git push heroku main

# Step 4: Run migrations
Write-Host ""
Write-Host "[4/4] Running database migrations on Heroku..." -ForegroundColor Yellow
& 'C:\Program Files\heroku\bin\heroku.cmd' run python migrate_pin.py -a godexroleplay

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "   Deploy completed!" -ForegroundColor Green
Write-Host "   URL: https://godexroleplay-8558d4eaa245.herokuapp.com/" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Read-Host "Press Enter to exit"
