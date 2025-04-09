# Star Wars Squadrons Score Reader

This project uses AI vision capabilities to extract and analyze scores from Star Wars Squadrons game screenshots, building a comprehensive database of match results and player statistics. It includes an ELO rating system to track team skill levels over time.

## Project Structure

```
Star Wars Squadrons Score Reader
│
├── ../Screenshots/             - Raw screenshots organized by season (outside project folder)
│   ├── SCL13/                  - Season 13 screenshots
│   ├── SCL14/                  - Season 14 screenshots
│   ├── SCL15/                  - Season 15 screenshots
│   ├── TEST/                   - Test screenshots
│   └── ...
│
├── Extracted Results/          - JSON files containing extracted match data
│   ├── SCL13/                  - Extracted data for Season 13
│   ├── SCL14/                  - Extracted data for Season 14
│   ├── ...
│   └── all_seasons_data.json   - Combined data from all seasons
│
├── score_extractor/            - Module for extracting data from screenshots
│   ├── __init__.py             - Main extraction logic using Claude API
│   ├── season_processor.py     - Process screenshots by season
│   └── test_extraction.py      - Test utilities for extraction
│
├── stats_reader/               - Module for processing data and managing the database
│   ├── elo_ladder.py           - ELO rating system for teams and players
│   ├── reference_manager.py    - Manages the reference database
│   ├── stats_db_processor.py   - Processes extracted data into the database
│   ├── ELO_LADDER_README.md    - Documentation for the ELO ladder
│   ├── README.md               - Documentation for stats processing
│   └── ...
│
├── stats_reports/              - Generated statistical reports
│   ├── elo_ladder.json         - Current ELO ratings
│   ├── elo_history.json        - History of ELO changes
│   └── ...
│
├── tests/                      - Unit tests for the project
│   ├── test_data/              - Test data fixtures
│   ├── test_score_extractor.py - Tests for score extraction
│   ├── test_stats_reader.py    - Tests for stats processing
│   └── test_reference_data.json- Test reference data
│
├── utilities/                  - Maintenance and diagnostic tools
│   ├── scan_screenshots.py     - Scan and organize screenshots
│   ├── update_paths.py         - Update file paths
│   └── README.md               - Documentation for utilities
│
├── env-setup.ps1               - PowerShell script for environment setup
├── squadrons_reference.db      - SQLite database with canonical player/team names
├── squadrons_stats.db          - SQLite database with all processed match data
└── README.md                   - This file
```

## Setup

1. Clone the repository:
   ```
   git clone https://github.com/Harry84/score-reader
   cd score-reader
   ```

2. Set up Python environment:
   ```powershell
   # Run the provided setup script to configure environment
   .\env-setup.ps1
   ```
   
   Or manually set up the environment:
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

4. Place your screenshots in the `../Screenshots` folder (at the same level as the project folder) in appropriately named subfolders

## Standard Workflow

1. **Add new screenshots** to the `../Screenshots` folder

2. **Process screenshots**:
   ```bash
   python -m score_extractor.season_processor --base-dir ../Screenshots --output-dir "Extracted Results"
   ```

3. **Populate the reference database**:
   ```bash
   python -m stats_reader.reference_manager --db squadrons_reference.db --populate-from-json "Extracted Results/all_seasons_data.json"
   ```

4. **Process data into database**:
   ```bash
   python -m stats_reader.stats_db_processor --input "Extracted Results/all_seasons_data.json" --reference-db squadrons_reference.db
   ```

5. **Fix pickup team IDs** (only if you have pickup matches):
   ```bash
   python -m stats_reader.fix_pickup_team_ids
   ```

6. **Generate ELO ladder**:
   ```bash
   python -m stats_reader.elo_ladder
   ```

## Processing a Single Folder

If you want to process only a specific folder of screenshots (e.g., just for testing):

1. **Process screenshots from a specific folder**:
   ```bash
   python -m score_extractor.season_processor --base-dir ../Screenshots --season TEST --output-dir "Extracted Results"
   ```
   This will process only the screenshots in the specified folder (TEST in this example) and save the results.

2. **Populate the reference database** from the extracted data:
   ```bash
   python -m stats_reader.reference_manager --db squadrons_reference.db --populate-from-json "Extracted Results/TEST/TEST_results.json"
   ```

3. **Process the extracted data into the stats database**:
   ```bash
   python -m stats_reader.stats_db_processor --input "Extracted Results/TEST/TEST_results.json" --reference-db squadrons_reference.db
   ```

4. **Fix team IDs for pickup matches** (if needed):
   ```bash
   python -m stats_reader.fix_pickup_team_ids
   ```

5. **Generate ELO ladder** (this will include only matches from the processed folder):
   ```bash
   python -m stats_reader.elo_ladder
   ```

## Workflow Components

Each step in the workflow corresponds to specific components in the project:

| Step | Component | Description |
|------|-----------|-------------|
| 1. Process Screenshots | `score_extractor/season_processor.py` | Extracts match data from screenshots using Claude API |
| 2. Populate Reference DB | `stats_reader/reference_manager.py` | Creates and manages the reference database for consistent player/team naming |
| 3. Process Data | `stats_reader/stats_db_processor.py` | Adds the extracted match data to the stats database |
| 4. Fix Pickup Team IDs | `stats_reader/fix_pickup_team_ids.py` | Sets team_id to NULL for pickup matches |
| 5. Generate ELO Ladder | `stats_reader/elo_ladder.py` | Calculates ELO ratings and generates ladders |

## Reference Database

The reference database (`squadrons_reference.db`) maintains consistent team and player names across matches. For advanced management:

```bash
python -m stats_reader.reference_manager --manage
```

This opens an interactive tool for managing canonical team and player names.

## Additional Tools

- **Stats Processing**: More details in `stats_reader/README.md`
- **ELO Ladder System**: Configuration and details in `stats_reader/ELO_LADDER_README.md`
- **Utilities**: Maintenance scripts documented in `utilities/README.md`

## Notes

- The project is configured to work with PNG and JPG files
- Extracted data is saved to the Extracted Results directory
- The SQLite database `squadrons_stats.db` contains all processed match data
- Reports are generated in the `stats_reports` directory
