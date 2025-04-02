# Game Score Extractor

This project uses Claude's AI vision capabilities to extract scores from game screenshots.

## Setup

1. Clone the repository code:
   `
   git clone https://github.com/yourusername/game-score-extractor
   cd game-score-extractor
   `

2. Make sure pyenv-win is installed

3. Set up Python environment:
   `powershell
   # Install Python (if not already installed)
   pyenv install 3.10.9
   
   # Set local Python version
   pyenv local 3.10.9
   
   # Create and activate virtual environment
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   
   # Install dependencies
   pip install -r requirements.txt
   `

4. Edit the .env file to add your Claude API key

5. Place your screenshots in the Screenshots folder

## Usage

Process all screenshots:
`powershell
python -m score_extractor.test_extraction --screenshots
`

Process a single image:
`powershell
python -m score_extractor.test_extraction Screenshots\your-image.jpg
`

## Notes
- The project is configured to work with PNG and JPG files
- Results will be saved to Screenshots/extraction_results.json
