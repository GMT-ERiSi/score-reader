# Player Role Implementation Guide

This guide details the changes needed to add player role support to the Star Wars Squadrons statistics system. Roles can be one of: "Farmer", "Flex", or "Support".

## 1. Reference Database Updates

### A. Add primary_role column to ref_players table

Open `reference_manager.py` and find the `initialize_db` method. Replace it with the content in `reference_manager_update.py`, or manually modify it to:

1. Add the `primary_role TEXT` column to the ref_players table creation
2. Add logic to check if the column exists and add it if it doesn't

### B. Update Reference Manager functions

In `reference_manager.py`, update the following functions to handle roles:

1. `add_player` - Add `primary_role` parameter
2. `get_player` - Include role in returned player data
3. `find_fuzzy_player_matches` - Include role in returned match data
4. `update_player` - Add support for updating player roles
5. `list_players` - Include role in returned player data

Use the updated functions in `reference_manager_functions.py` as templates.

### C. Update Interactive Player Management

Replace or update the `interactive_player_management` function in `reference_manager.py` to handle roles with:

1. Add "List players by role" option
2. Update player display to show roles
3. Add role selection when adding a new player
4. Add role editing when updating a player

Use the updated function in `interactive_player_management.py` as a template.

## 2. Stats Database Updates

### A. Add role column to player_stats table

Open `modules/database_utils.py` and update the `create_database` function to:

1. Add the `role TEXT` column to the player_stats table creation
2. Add logic to check if the column exists and add it if it doesn't

Use the code in `modules/database_utils_update.py` as a template.

### B. Update Player Stats Processing

Open `modules/player_processor.py` and update the `process_player_stats` function to:

1. Get the player's primary role from reference database
2. Allow overriding the role for each match
3. Store the role value in the player_stats table

Use the code in `modules/player_processor_update.py` as a template.

### C. Update Report Generation

Open `modules/report_generator.py` and:

1. Update all player-related queries to include the role field
2. Add new functions for role-based reports:
   - `generate_role_based_reports` to create reports filtered by role
   - `generate_role_distribution_report` to show statistics about roles
3. Add role to player_teams and subbing_report

Use the code in `modules/report_generator_update.py` as a template.

## 3. Testing Steps

1. Create a new reference database or update an existing one:
   ```bash
   python -m stats_reader.reference_manager --db squadrons_reference_test.db --manage
   ```

2. Assign primary roles to players using the player management menu:
   - Use option "2. Player Management"
   - Use option "5. Edit a player" to assign roles to existing players
   - Use option "4. Add a new player" when adding new players
   - Use option "3. List players by role" to verify roles have been assigned correctly

3. Process some match data with the updated system:
   ```bash
   python -m stats_reader.stats_db_processor_direct --input "Extracted Results\SCL15\SCL15_results.json" --reference-db squadrons_reference_test.db --db squadrons_stats_test.db
   ```
   
4. During processing, observe:
   - Primary roles should be applied automatically from the reference database
   - You should be able to override the role for specific matches
   - Confirm the data is being properly stored

5. Check the generated reports for role information:
   - `player_performance.json` should include role information
   - New role-specific reports should be created:
     - `player_performance_role_farmer.json`
     - `player_performance_role_flex.json` 
     - `player_performance_role_support.json`
   - `role_distribution.json` should show statistics about roles
   - `role_distribution_by_match_type.json` should show role statistics by match type

## 4. Updating Existing Data

If you already have a database with existing player stats and want to add roles:

1. The database schema updates will add the role column to existing tables
2. For historical matches, the role will be NULL
3. You can update roles for specific players by editing the database directly:

```sql
-- Update specific player's role in all matches
UPDATE player_stats 
SET role = 'Farmer' 
WHERE player_name = 'PlayerName';

-- Update specific player's role in specific match type
UPDATE player_stats 
SET role = 'Support' 
WHERE player_name = 'PlayerName'
AND match_id IN (
    SELECT id FROM matches WHERE match_type = 'team'
);
```

## 5. Filtering ELO Ladders

To filter ELO ladders by role, you'll need to update the ELO ladder generation scripts:

1. In `elo_ladder.py` and `player_elo_ladder.py`, add a `--role` option:
   ```python
   parser.add_argument("--role", type=str, choices=["Farmer", "Flex", "Support"],
                      help="Filter players by role")
   ```

2. Add filtering logic to the player selection in the ELO calculation:
   ```python
   # When processing matches for player ELO
   if args.role:
       # Add role filter to SQL queries
       cursor.execute("""
       SELECT ...
       FROM player_stats ps
       WHERE ps.role = ?
       ...
       """, (args.role,))
   ```

3. Update the output filename to indicate role filtering:
   ```python
   if args.role:
       output_filename = f"{args.match_type}_player_elo_ladder_{args.role.lower()}.json"
   else:
       output_filename = f"{args.match_type}_player_elo_ladder.json"
   ```

## 6. Summary of New Generated Reports

After implementation, you will have the following new reports:

- `player_performance_role_farmer.json` - Statistics for players with Farmer role
- `player_performance_role_flex.json` - Statistics for players with Flex role
- `player_performance_role_support.json` - Statistics for players with Support role
- Role-based reports for each match type (team, pickup, ranked)
- `role_distribution.json` - Overall role statistics
- `role_distribution_by_match_type.json` - Role statistics by match type

Additionally, all existing player reports will include the role information.
