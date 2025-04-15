# Star Wars Squadrons Score Reader

This project uses AI vision capabilities to extract and analyze scores from Star Wars Squadrons game screenshots, building a comprehensive database of match results and player statistics. It includes ELO rating systems to track both team and individual player skill levels.

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
│   ├── elo_ladder.py           - ELO rating system for teams
│   ├── player_elo_ladder.py    - ELO rating system for individual players (pickup/ranked)
│   ├── reference_manager.py    - Manages the reference database
│   ├── stats_db_processor.py   - Processes extracted data into the database
│   ├── stats_db_processorV5.py - Enhanced processor with pickup/ranked match support
│   ├── ELO_LADDER_README.md    - Documentation for the ELO ladder
│   ├── README.md               - Documentation for stats processing
│   └── ...
│
├── stats_reports/              - Generated statistical reports
│   ├── elo_ladder.json         - Current ELO ratings for teams
│   ├── elo_history.json        - History of ELO changes for teams
│   ├── pickup_player_elo_ladder.json - ELO ratings for players in pickup matches
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

## Standard Workflow for Team Matches

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

6. **Generate ELO ladder**:
   ```bash
   python -m stats_reader.elo_ladder
   ```

## Workflow for Pickup/Ranked Matches

For processing pickup or ranked matches (where players are not representing established teams):

1. **Process screenshots** as in the standard workflow:
   ```bash
   python -m score_extractor.season_processor --base-dir ../Screenshots --season [FOLDER] --output-dir "Extracted Results"
   ```

2. **Clean the extracted data**:
   ```bash
   python -m stats_reader clean --input "Extracted Results/[FOLDER]/[FOLDER]_results.json" --output "Extracted Results/[FOLDER]/[FOLDER]_results_cleaned.json"
   ```

3. **Process the data as pickup/ranked matches**:
   ```bash
   # Create a dedicated database for pickup/ranked matches (recommended)
   python -m stats_reader.stats_db_processorV5 --input "Extracted Results/[FOLDER]/[FOLDER]_results_cleaned.json" --db squadrons_stats_pickup.db --reference-db squadrons_reference.db
   ```
   
   When prompted during processing:
   - Choose "pickup" or "ranked" as the match type
   - The processor will automatically:
     - Assign generic team names ("Imp_pickup_team"/"NR_pickup_team" or "Imperial_ranked_team"/"NR_ranked_team")
     - Set player team_ids to NULL for proper pickup/ranked tracking

4. **Generate player-based ELO ladder**:
   ```bash
   python -m stats_reader.player_elo_ladder --db squadrons_stats_pickup.db --output "stats_reports_pickup" --match-type pickup
   ```
   
   This will create:
   - `pickup_player_elo_ladder.json`: Current ELO ratings for individual players
   - `pickup_player_elo_history.json`: Full history of player ELO changes

   For ranked matches, use `--match-type ranked` instead.

5. **View generated reports** in the `stats_reports_pickup` directory to analyze player performance.

## Key Differences between Team and Pickup/Ranked Processing

- **Team Assignment**: In team matches, players represent specific teams. In pickup/ranked matches, players play for themselves regardless of their primary team affiliation.
- **ELO Calculation**: Team matches use team-based ELO. Pickup/ranked matches use player-based ELO.
- **Database Handling**: For pickup/ranked matches, player team_ids are set to NULL in the database, but the matches themselves still maintain faction assignments (Imperial/Rebel).
- **Reports**: Pickup/ranked matches generate player-centric reports rather than team-centric ones.

## Processing a Single Folder

If you want to process only a specific folder of screenshots (e.g., for a season of team games or a batch of pickup games or just for testing):

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
   # For team matches
   python -m stats_reader.stats_db_processor --input "Extracted Results/TEST/TEST_results_cleaned.json" --reference-db squadrons_reference.db
   
   # OR for pickup/ranked matches
   python -m stats_reader.stats_db_processorV5 --input "Extracted Results/TEST/TEST_results_cleaned.json" --db squadrons_stats_pickup.db --reference-db squadrons_reference.db
   ```
   
   When using V5 processor for pickup/ranked matches, select the appropriate match type when prompted.

5. **Generate appropriate ELO ladder**:
   ```bash
   # For team matches
   python -m stats_reader.elo_ladder
   
   # OR for pickup/ranked matches
   python -m stats_reader.player_elo_ladder --db squadrons_stats_pickup.db --match-type pickup
   ```

## Workflow Components

Each step in the workflow corresponds to specific components in the project:

| Step | Component | Description |
|------|-----------|-------------|
| 1. Process Screenshots | `score_extractor/season_processor.py` | Extracts match data from screenshots using Claude API |
| 2. Clean Extracted Data | `stats_reader clean` | Interactive tool to correct AI extraction errors (scores, teams, results) |
| 3a. Populate Reference DB | `stats_reader/reference_manager.py` | Creates the reference database with player names from cleaned data |
| 3b. Manage Reference DB | `stats_reader/reference_manager.py --manage` | Interactive tool for setting player primary teams and resolving duplicate player names |
| 4a. Process Team Data | `stats_reader/stats_db_processor.py` | Adds the cleaned team match data to the stats database |
| 4b. Process Pickup/Ranked Data | `stats_reader/stats_db_processorV5.py` | Processes pickup/ranked matches with proper handling |
| 5a. Generate Team ELO | `stats_reader/elo_ladder.py` | Calculates team ELO ratings and generates ladders |
| 5b. Generate Player ELO | `stats_reader/player_elo_ladder.py` | Calculates individual player ELO ratings for pickup/ranked matches |

## Reference Database

The reference database (`squadrons_reference.db`) maintains consistent team and player names across matches. For advanced management:

```bash
python -m stats_reader.reference_manager --manage
```

This opens an interactive tool for managing canonical team and player names.

## Player Subbing System

The project tracks whether players are 'subbing' (playing for a team that is not their primary team) to differentiate between regular team appearances and substitute appearances. Here's how it works:

### How Subbing is Determined

1. **During Import**: The subbing status (is_subbing = 0 or 1) is determined and stored when match data is imported via `stats_db_processor.py`.

2. **Reference-Based Suggestion**: When importing match data, the system compares:
   - The player's primary team in the reference database
   - The team they're playing for in the current match

3. **User Confirmation**: The system suggests a subbing status (Yes/No) based on team name comparison, but you can override this suggestion during import by answering Yes/No to the prompt.

4. **Permanent Storage**: Once confirmed, the subbing status is permanently stored in the database with that player's stats for that match. It is not recalculated later.

### Important Note About Player Transfers

If a player changes teams between seasons:

- **Option 1**: Update their primary team in the reference database using `reference_manager`.
  ```bash
  python -m stats_reader.reference_manager --db squadrons_reference.db --manage
  ```
  Then select Player Management → Edit Player → Update Primary Team.

- **Option 2**: During import, simply reject the suggested subbing status if it doesn't reflect the historical reality of whether they were subbing at that time.

The crucial detail is that **subbing status is determined and fixed at import time**, not dynamically recalculated based on the current reference database. The reference database only provides default suggestions during import.

### How Subbing Affects Reports

The system generates several reports that use the subbing status differently:

- `player_performance.json`: Includes ALL games, regardless of subbing status
- `player_performance_no_subs.json`: Only includes games where is_subbing = 0 (regular team appearances)
- `subbing_report.json`: Only shows games where is_subbing = 1 (substitute appearances)

## Pickup/Ranked Stats and ELO

For pickup and ranked matches, the system takes a different approach:

- **No Team Assignment**: Players are not associated with teams (team_id is NULL)
- **Faction-Based Stats**: Players are still tracked based on their faction (Imperial/Rebel)
- **Player-Centric ELO**: The ELO system rates individual players instead of teams
- **Specialized Reports**: Dedicated reports track player performance in pickup/ranked matches

The player ELO system works by:
1. Calculating the average ELO of all players on each faction in a match
2. Updating individual player ratings based on match outcomes
3. Ranking players based on their personal skill level

## Additional Tools

- **Stats Processing**: More details in `stats_reader/README.md`
- **ELO Ladder System**: Configuration and details in `stats_reader/ELO_LADDER_README.md`
- **Utilities**: Maintenance scripts documented in `utilities/README.md`

## Notes

- The project is configured to work with PNG and JPG files
- Extracted data is saved to the Extracted Results directory
- The SQLite database `squadrons_stats.db` contains all processed match data
- Reports are generated in the `stats_reports` directory
