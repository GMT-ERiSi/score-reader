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

These utilities are not part of the regular workflow. For normal usage of the Star Wars Squadrons Score Reader, follow these steps:

1. Add new screenshots to the Screenshots folder
2. Process screenshots: `python -m score_extractor.season_processor`
3. Process data into database: `python -m stats_reader.stats_db_processor`
4. Generate ELO ladder: `python -m stats_reader elo`

## Notes

- The `scan_screenshots.py` script expects the Screenshots folder to be at the same level as the project folder
- The `update_paths.py` script requires an existing database to work with
- Both scripts can be run multiple times without causing harm
- Always make a backup of your database before making significant changes
