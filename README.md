# Star Wars Squadrons Score Reader

This project uses Claude's AI vision capabilities to extract and analyze scores from Star Wars Squadrons game screenshots, building a comprehensive database of match results and player statistics.

## Setup

1. Clone the repository code:
   ```
   git clone https://github.com/Harry84/score-reader
   cd score-reader
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

4. Edit the .env file to add your Claude API key

5. Place your screenshots in the Screenshots folder

## Usage

### Extract scores from screenshots
Process all screenshots:
```powershell
python -m score_extractor.test_extraction --screenshots
```

Process a single image:
```powershell
python -m score_extractor.test_extraction Screenshots\your-image.jpg
```

### Process scores by season
```powershell
python -m score_extractor.season_processor --base-dir Screenshots
```

### Stats Processing and ELO Ladder

For detailed instructions on stats processing, database management, and the ELO ladder feature, refer to the README.md file in the stats_reader directory.

Basic usage:

```powershell
# Set up reference database (one-time setup)
python -m stats_reader reference

# Clean extracted data
python -m stats_reader clean --input Screenshots/all_seasons_data.json --output Screenshots/all_seasons_data_cleaned.json

# Process data into database
python -m stats_reader process --input Screenshots/all_seasons_data_cleaned.json --reference-db squadrons_reference.db

# Generate ELO ladder
python -m stats_reader elo
```

## Project Structure
- `score_extractor/`: Module for extracting data from screenshots
- `stats_reader/`: Module for processing data and managing the database (see its README for details)
- `stats_reports/`: Generated statistical reports
- `Screenshots/`: Directory for storing game screenshots

## Notes
- The project is configured to work with PNG and JPG files
- Extracted data is saved to Screenshots/extraction_results.json
- The SQLite database `squadrons_stats.db` contains all processed match data
- Reports are generated in the `stats_reports` directory