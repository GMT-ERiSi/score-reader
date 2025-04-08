# Star Wars Squadrons Score Reader

This project uses AI vision capabilities to extract and analyze scores from Star Wars Squadrons game screenshots, building a comprehensive database of match results and player statistics. It includes an ELO rating system to track team skill levels over time.

## Directory Structure

- `../Screenshots/` - Raw screenshots organized by season (outside project folder)
- `./Extracted Results/` - JSON files containing extracted match data
- `./score_extractor/` - Module for extracting data from screenshots
- `./stats_reader/` - Module for processing data and managing the database
- `./stats_reports/` - Generated statistical reports
- `./utilities/` - Maintenance and diagnostic tools

## Setup

1. Clone the repository:
   ```
   git clone https://github.com/Harry84/score-reader
   cd score-reader
   ```

2. Set up Python environment:
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

3. Edit the .env file to add your Claude API key

4. Place your screenshots in the `../Screenshots` folder (at the same level as the project folder)

## Standard Workflow

1. **Add new screenshots** to the `../Screenshots` folder

2. **Process screenshots**:
   ```bash
   python -m score_extractor.season_processor --base-dir ../Screenshots --output-dir "Extracted Results"
   ```

3. **Clean the extracted data**:
   ```bash
   python -m stats_reader clean --input "Extracted Results/all_seasons_data.json" --output "Extracted Results/all_seasons_data_cleaned.json"
   ```
   This interactive tool allows you to verify and correct the AI-extracted data.

4. **Process data into database**:
   ```bash
   python -m stats_reader.stats_db_processor --input "Extracted Results/all_seasons_data_cleaned.json" --reference-db squadrons_reference.db
   ```

5. **Update match dates** (only if needed):
   ```bash
   python utilities/update_paths.py
   ```
   This step is only necessary if dates couldn't be automatically extracted from screenshot filenames.

6. **Generate ELO ladder**:
   ```bash
   python -m stats_reader elo
   ```

## Detailed Documentation

- For details on statistical processing and the ELO ladder, see the `stats_reader/README.md` file
- For utility scripts and maintenance tasks, see the `utilities/README.md` file

## Reference Database

The reference database (`squadrons_reference.db`) maintains consistent team and player names across matches. To set it up:

```bash
python -m stats_reader reference
```

This opens an interactive tool for managing canonical team and player names.

## Notes

- The project is configured to work with PNG and JPG files
- Extracted data is saved to the Extracted Results directory
- The SQLite database `squadrons_stats.db` contains all processed match data
- Reports are generated in the `stats_reports` directory
