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

   # Or manually set up the environment:  
   # Note: These instructions assume pyenv-win is installed. If not, you can install it or use 
   # a regular Python installation instead of 3.10.9 (if not already installed)
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

4. Place your screenshots in the `../Screenshots` folder (at the same level as the project folder) in the appropriately named folder

## Standard Workflow

1. **Add new screenshots** to the appropriate folder in the `../Screenshots` folder

2. **Process screenshots**:
   ```bash
   python -m score_extractor.season_processor --base-dir ../Screenshots --output-dir "Extracted Results"
   ```
   This generates `Extracted Results/all_seasons_data.json`.

3. **Clean the extracted data** (Recommended):
   ```bash
   python -m stats_reader clean --input "Extracted Results/all_seasons_data.json" --output "Extracted Results/all_seasons_data_cleaned.json"
   ```
   This launches an interactive tool to review and correct potential AI extraction errors (scores, team names, results) by comparing against the original screenshots. Don't worry about slightly different player names for the same person here; that's handled in the next step.

4. **Populate and manage the reference database**:
   ```bash
   # Start fresh by deleting any existing reference database if needed
   # del squadrons_reference.db
   
   # Populate the reference database with player names from the CLEANED data
   python -m stats_reader.reference_manager --db squadrons_reference.db --populate-from-json "Extracted Results/all_seasons_data_cleaned.json"
   
   # Then manage teams and players using the interactive tool
   python -m stats_reader.reference_manager --db squadrons_reference.db --manage
   ```
   
   When using the management interface:
   1. Choose "Team Management" to first create any teams you need.
   2. Then select "Player Management" to assign players to their primary teams and use "Resolve Duplicate Player IDs" to merge different names for the same player (e.g., "PlayerA" and "Player A") into a single canonical entry. This also updates the `_cleaned.json` file for consistency.
   
   Setting primary teams is important for tracking substitute appearances.

5. **Process data into database**:
   ```bash
   # Use the CLEANED data as input
   python -m stats_reader.stats_db_processor --input "Extracted Results/all_seasons_data_cleaned.json" --reference-db squadrons_reference.db
   ```

6. **Fix pickup team IDs** (only if processing pickup/ranked matches):
   ```bash
   python -m stats_reader.fix_pickup_team_ids
   ```

7. **Generate ELO ladder**:
   ```bash
   python -m stats_reader.elo_ladder
   ```

## Processing a Single Folder

If you want to process only a specific folder of screenshots (e.g., just for testing):

1. **Process screenshots from a specific folder**:
   ```bash
   # Example using TEST folder
   python -m score_extractor.season_processor --base-dir ../Screenshots --season TEST --output-dir "Extracted Results"
   ```
   This processes only the `TEST` folder and saves results to `Extracted Results/TEST/TEST_results.json`.

2. **Clean the extracted data** (Recommended):
   ```bash
   # Example using TEST folder output
   python -m stats_reader clean --input "Extracted Results/TEST/TEST_results.json" --output "Extracted Results/TEST/TEST_results_cleaned.json"
   ```
   Review and correct potential AI extraction errors (scores, team names, results) against the screenshots for this specific folder. Don't worry about slightly different player names for the same person here.

3. **Populate and manage the reference database**:
   ```bash
   # Start fresh if necessary by deleting any existing reference database
   # del squadrons_reference.db
   
   # Populate the reference database with player names from the CLEANED data
   python -m stats_reader.reference_manager --db squadrons_reference.db --populate-from-json "Extracted Results/TEST/TEST_results_cleaned.json"
   
   # Then manage teams and players using the interactive tool
   python -m stats_reader.reference_manager --db squadrons_reference.db --manage
   ```
   
   When using the management interface:
   1. Create teams if needed.
   2. Assign primary teams and use "Resolve Duplicate Player IDs" to merge different names for the same player. This also updates the `_cleaned.json` file.

4. **Process the extracted data into the stats database**:
   ```bash
   # Use the CLEANED data as input
   python -m stats_reader.stats_db_processor --input "Extracted Results/TEST/TEST_results_cleaned.json" --reference-db squadrons_reference.db
   ```

5. **Fix team IDs for pickup matches** (if needed):
   ```bash
   python -m stats_reader.fix_pickup_team_ids
   ```

6. **Generate ELO ladder** (will include only matches from the processed folder):
   ```bash
   python -m stats_reader.elo_ladder
   ```

## Workflow Components

Each step in the workflow corresponds to specific components in the project:

| Step | Component | Description |
|------|-----------|-------------|
| 1. Process Screenshots | `score_extractor/season_processor.py` | Extracts match data from screenshots using Claude API |
| 2. Clean Extracted Data | `stats_reader clean` | Interactive tool to correct AI extraction errors (scores, teams, results) |
| 3a. Populate Reference DB | `stats_reader/reference_manager.py` | Creates the reference database with player names from cleaned data |
| 3b. Manage Reference DB | `stats_reader/reference_manager.py --manage` | Interactive tool for setting player primary teams and resolving duplicate player names |
| 4. Process Data | `stats_reader/stats_db_processor.py` | Adds the cleaned match data to the stats database |
| 5. Fix Pickup Team IDs | `stats_reader/fix_pickup_team_ids.py` | Sets team_id to NULL for pickup matches |
| 6. Generate ELO Ladder | `stats_reader/elo_ladder.py` | Calculates ELO ratings and generates ladders |

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
