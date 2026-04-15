@echo off
setlocal EnableExtensions
:: ═══════════════════════════════════════════════
::  Sentinel Release Helper
::  Usage: build-release.bat 1.0.0
::  This tags your commit and pushes it to GitHub.
::  GitHub Actions will then build the zips automatically.
:: ═══════════════════════════════════════════════

:: Check a version was provided
if "%~1"=="" (
    echo.
    echo  ERROR: No version number provided.
    echo  Usage: build-release.bat 1.0.0
    echo.
    pause
    exit /b 1
)

set "INPUT_VERSION=%~1"
set "RAW_VERSION=%INPUT_VERSION%"

:: Accept both X.Y.Z and vX.Y.Z by stripping one leading v/V if present.
if /i "%RAW_VERSION:~0,1%"=="v" set "RAW_VERSION=%RAW_VERSION:~1%"

echo(%RAW_VERSION%| findstr /R /C:"^[0-9][0-9]*\.[0-9][0-9]*\.[0-9][0-9]*$" >nul
if errorlevel 1 (
    echo.
    echo  ERROR: Invalid version "%INPUT_VERSION%".
    echo  Use X.Y.Z or vX.Y.Z ^(example: 1.2.3 or v1.2.3^)
    echo.
    pause
    exit /b 1
)

set "VERSION=v%RAW_VERSION%"

echo.
echo  Releasing %VERSION%...
echo.

:: Ensure we're in a git repository
git rev-parse --is-inside-work-tree >nul 2>nul
if errorlevel 1 (
    echo  ERROR: This folder is not a git repository.
    pause
    exit /b 1
)

:: Make sure we're on the main branch
set BRANCH=
for /f "delims=" %%i in ('git rev-parse --abbrev-ref HEAD 2^>nul') do set BRANCH=%%i
if "%BRANCH%"=="" (
    echo  ERROR: Unable to determine current branch.
    pause
    exit /b 1
)

if /i not "%BRANCH%"=="main" (
    echo  WARNING: You are on branch "%BRANCH%", not "main".
    set /p CONFIRM= Continue anyway? [y/N]: 
    if /i not "%CONFIRM%"=="y" (
        echo  Aborted.
        pause
        exit /b 1
    )
)

:: Check for uncommitted changes
set HAS_CHANGES=
for /f "delims=" %%i in ('git status --porcelain') do set HAS_CHANGES=1
if defined HAS_CHANGES (
    echo  WARNING: You have uncommitted changes.
    set /p CONFIRM2= Continue anyway? [y/N]: 
    if /i not "%CONFIRM2%"=="y" (
        echo  Aborted. Commit or stash your changes first.
        pause
        exit /b 1
    )
)

:: Ensure tag does not already exist locally
git rev-parse -q --verify "refs/tags/%VERSION%" >nul 2>nul
if not errorlevel 1 (
    echo  ERROR: Local tag %VERSION% already exists.
    echo  Delete it first: git tag -d %VERSION%
    pause
    exit /b 1
)

:: Ensure tag does not already exist on remote
git ls-remote --exit-code --tags origin "refs/tags/%VERSION%" >nul 2>nul
if not errorlevel 1 (
    echo  ERROR: Remote tag %VERSION% already exists on origin.
    echo  Choose a new version number.
    pause
    exit /b 1
)

:: Create the tag
echo  Creating tag %VERSION%...
git tag %VERSION%
if errorlevel 1 (
    echo  ERROR: Failed to create tag. It may already exist.
    echo  To delete an existing tag: git tag -d %VERSION%
    pause
    exit /b 1
)

:: Push the tag to GitHub — this triggers the Actions workflow
echo  Pushing tag to GitHub...
git push origin %VERSION%
if errorlevel 1 (
    echo  ERROR: Failed to push tag.
    echo  Deleting local tag to keep things clean...
    git tag -d %VERSION%
    pause
    exit /b 1
)

echo.
echo  ═══════════════════════════════════════════
echo   Done! Tag %VERSION% pushed to GitHub.
echo   GitHub Actions is now building your release.
echo.
echo   Watch progress on your repository Actions page.
echo   Release will appear on your repository Releases page.
echo  ═══════════════════════════════════════════
echo.
pause