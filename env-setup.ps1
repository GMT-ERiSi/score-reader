# Minimal Setup Script for Game Score Extractor
# This script creates just the basic folder structure and configuration files
# Project code should be pulled separately from GitHub

# Function to check if pyenv-win is installed
function Test-PyenvInstalled {
    try {
        $pyenvVersion = (pyenv --version)
        return $true
    } catch {
        return $false
    }
}

# Function to check if a Python version is installed
function Test-PythonVersionInstalled {
    param(
        [string]$Version
    )
    
    $installedVersions = (pyenv versions)
    return ($installedVersions -match $Version)
}

# Repository URL for the readme
$repoUrl = "https://github.com/yourusername/game-score-extractor"

# Create project structure
Write-Host "Creating minimal project structure..." -ForegroundColor Green
$projectRoot = $PWD.Path
$screenshotsDir = Join-Path -Path $projectRoot -ChildPath "Screenshots"

# Create Screenshots directory if it doesn't exist
if (-not (Test-Path $screenshotsDir)) {
    New-Item -Path $screenshotsDir -ItemType Directory
    Write-Host "Created Screenshots directory" -ForegroundColor Cyan
} else {
    Write-Host "Screenshots directory already exists" -ForegroundColor Yellow
}

# Create local.settings.json for local development
$localSettingsPath = Join-Path -Path $projectRoot -ChildPath "local.settings.json"
if (-not (Test-Path $localSettingsPath)) {
    @"
{
  "IsEncrypted": false,
  "Values": {
    "AzureWebJobsStorage": "UseDevelopmentStorage=true",
    "FUNCTIONS_WORKER_RUNTIME": "python",
    "ANTHROPIC_API_KEY": "your-api-key-here"
  }
}
"@ | Out-File -FilePath $localSettingsPath -Encoding utf8
    Write-Host "Created local.settings.json template" -ForegroundColor Cyan
} else {
    Write-Host "local.settings.json already exists" -ForegroundColor Yellow
}

# Create .env file for API key
$envFilePath = Join-Path -Path $projectRoot -ChildPath ".env"
if (-not (Test-Path $envFilePath)) {
    @"
# Claude API key - replace with your actual key
ANTHROPIC_API_KEY=your-api-key-here
"@ | Out-File -FilePath $envFilePath -Encoding utf8
    Write-Host "Created .env file for API key (please edit this with your actual API key)" -ForegroundColor Cyan
} else {
    Write-Host ".env file already exists" -ForegroundColor Yellow
}

# Create a .gitignore file
$gitignorePath = Join-Path -Path $projectRoot -ChildPath ".gitignore"
if (-not (Test-Path $gitignorePath)) {
    @"
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual Environment
venv/
env/
ENV/

# Environment variables and secrets
.env
local.settings.json

# Azure Function artifacts
bin/
obj/
.python_packages/

# IDE files
.vscode/
.idea/
*.swp
*.swo

# Operating System Files
.DS_Store
Thumbs.db

# Extraction Results
Screenshots/extraction_results.json
"@ | Out-File -FilePath $gitignorePath -Encoding utf8
    Write-Host "Created .gitignore file" -ForegroundColor Cyan
} else {
    Write-Host ".gitignore already exists" -ForegroundColor Yellow
}

# Create a minimal README.md with instructions
$readmePath = Join-Path -Path $projectRoot -ChildPath "README.md"
if (-not (Test-Path $readmePath)) {
    @"
# Game Score Extractor

This project uses Claude's AI vision capabilities to extract scores from game screenshots.

## Setup

1. Clone the repository code:
   ```
   git clone $repoUrl
   cd game-score-extractor
   ```

2. Make sure pyenv-win is installed

3. Set up Python environment:
   ```powershell
   # Install Python (if not already installed)
   pyenv install 3.10.9
   
   # Set local Python version
   pyenv local 3.10.9
   
   # Create and activate virtual environment
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   
   # Install dependencies
   pip install -r requirements.txt
   ```

4. Edit the `.env` file to add your Claude API key

5. Place your screenshots in the `Screenshots` folder

## Usage

Process all screenshots:
```powershell
python -m score_extractor.test_extraction --screenshots
```

Process a single image:
```powershell
python -m score_extractor.test_extraction Screenshots\your-image.jpg
```

## Notes
- The project is configured to work with PNG and JPG files
- Results will be saved to `Screenshots/extraction_results.json`
"@ | Out-File -FilePath $readmePath -Encoding utf8
    Write-Host "Created README.md with instructions" -ForegroundColor Cyan
} else {
    Write-Host "README.md already exists" -ForegroundColor Yellow
}

# Set up Python environment with pyenv-win
if (Test-PyenvInstalled) {
    Write-Host "pyenv-win is installed" -ForegroundColor Green
    
    # Check Python version - we'll use 3.10.9 for this project
    $pythonVersion = "3.10.9"
    
    if (Test-PythonVersionInstalled -Version $pythonVersion) {
        Write-Host "Python $pythonVersion is already installed" -ForegroundColor Green
    } else {
        Write-Host "Installing Python $pythonVersion..." -ForegroundColor Yellow
        pyenv install $pythonVersion
    }
    
    # Set local Python version for this project
    Write-Host "Setting local Python version to $pythonVersion for this project" -ForegroundColor Cyan
    pyenv local $pythonVersion
    
    # Create virtual environment
    $venvPath = Join-Path -Path $projectRoot -ChildPath "venv"
    if (-not (Test-Path $venvPath)) {
        Write-Host "Creating virtual environment..." -ForegroundColor Cyan
        python -m venv $venvPath
    } else {
        Write-Host "Virtual environment already exists" -ForegroundColor Yellow
    }
    
    # Final instructions
    Write-Host "`nMinimal setup completed!" -ForegroundColor Green
    Write-Host "`nNext steps:" -ForegroundColor Magenta
    Write-Host "1. Pull the code from GitHub: git clone $repoUrl" -ForegroundColor White
    Write-Host "2. Activate the virtual environment: .\venv\Scripts\Activate.ps1" -ForegroundColor White
    Write-Host "3. Install dependencies: pip install -r requirements.txt" -ForegroundColor White
    Write-Host "4. Edit the .env file with your Claude API key" -ForegroundColor White
    Write-Host "5. Add your screenshots to the Screenshots folder" -ForegroundColor White
    
} else {
    Write-Host "pyenv-win is not installed! Please install it first: " -ForegroundColor Red
    Write-Host "https://github.com/pyenv-win/pyenv-win#installation" -ForegroundColor Cyan
}