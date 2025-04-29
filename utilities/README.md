# Utility Scripts

This folder contains utility scripts that help with maintenance, diagnostics, and data management tasks for the Star Wars Squadrons Score Reader project. These scripts are not part of the regular workflow but serve as helpful tools during setup and troubleshooting.

## Available Utilities

### scan_screenshots.py

**Purpose**: Diagnostic tool to verify screenshot detection and organization.

**When to use**: 
- After moving your project to a new directory structure
- When you want to verify that your code can find screenshots
- To check if screenshots are properly organized by season
- To compare database entries with available screenshots

**Usage**:
```bash
python utilities/scan_screenshots.py
```

With custom screenshots path:
```bash
python utilities/scan_screenshots.py --dir "path/to/screenshots"
```

### update_paths.py

**Purpose**: Update match dates in the database to ensure correct chronological ordering.

**When to use**:
- After initial database setup to set accurate match dates
- When ELO calculations need to be corrected due to date issues
- When adding new matches that need specific dates

**Usage**:
```bash
python utilities/update_paths.py
```

With custom database path:
```bash
python utilities/update_paths.py --db "path/to/database.db"
```

## Standard Workflow

For normal usage of the Star Wars Squadrons Score Reader, follow these steps:

1. **Add new screenshots** to the ../Screenshots folder

2. **Process screenshots**:
   ```bash
   python -m score_extractor.season_processor --base-dir ../Screenshots --output-dir "Extracted Results"
   ```

3. **Clean the extracted data**:
   ```bash
   python -m stats_reader clean --input "Extracted Results/all_seasons_data.json" --output "Extracted Results/all_seasons_data_cleaned.json"
   ```

4. **Process data into database**:
   ```bash
   python -m stats_reader.stats_db_processor --input "Extracted Results/all_seasons_data_cleaned.json" --reference-db squadrons_reference.db
   ```

5. **Update match dates** (only needed if automatic extraction from filenames failed):
   ```bash
   python utilities/update_paths.py
   ```

6. **Generate ELO ladder**:
   ```bash
   python -m stats_reader elo
   ```

## Database Recreation Steps

To completely recreate your `squadrons_stats.db` database from scratch:

1. **Delete the existing database**:
   ```bash
   del squadrons_stats.db
   ```

2. **Process your screenshots data**:
   ```bash
   python -m score_extractor.season_processor --base-dir ../Screenshots --output-dir "Extracted Results"
   ```
   This will process all screenshots and save the results to the "Extracted Results" folder.

3. **Clean the extracted data** (important step to verify AI-extracted data against screenshots):
   ```bash
   python -m stats_reader clean --input "Extracted Results/all_seasons_data.json" --output "Extracted Results/all_seasons_data_cleaned.json"
   ```
   This launches an interactive tool that allows you to:
   - Review each match's data
   - Compare with the original screenshots
   - Edit team names, match results, and player stats
   - Fix any errors from the AI extraction

4. **Setup reference database** (optional but recommended for team/player consistency):
   ```bash
   python -m stats_reader reference --db squadrons_reference.db
   ```
   The reference database helps maintain consistent:
   - Team names (even with spelling variations)
   - Player identities (across different teams)
   - Tracking of player team affiliations

5. **Create and populate the new database**:
   ```bash
   python -m stats_reader.stats_db_processor --input "Extracted Results/all_seasons_data_cleaned.json" --reference-db squadrons_reference.db
   ```
   Using the reference database (if created) will:
   - Suggest team names based on recognized players
   - Standardize player names across matches
   - Track when players are subbing for other teams

6. **Update match dates** (only needed if automatic extraction from filenames failed):
   ```bash
   python utilities/update_paths.py
   ```

7. **Generate the ELO ladder**:
   ```bash
   python -m stats_reader elo
   ```

## Notes

- The `scan_screenshots.py` script expects the Screenshots folder to be at the same level as the project folder
- The `update_paths.py` script requires an existing database to work with
- Both scripts can be run multiple times without causing harm
- Always make a backup of your database before making significant changes
- You can safely delete the old Screenshots folder inside the project directory after migrating to the new structure
