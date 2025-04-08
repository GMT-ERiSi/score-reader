# ELO Ladder System for Star Wars Squadrons

This system supports multiple ELO ladders for different match types:

1.  **Team ELO Ladder** - For organized team matches (`match_type = 'team'`)
2.  **Pickup Player ELO Ladder** - For individual player rankings from custom pickup matches (`match_type = 'pickup'`)
3.  **Ranked Player ELO Ladder** - For individual player rankings from ranked queue matches (`match_type = 'ranked'`)

## Workflow Overview

1.  **Process Match Data:** Add match results from JSON files to the database using `stats_db_processor.py`. You will be prompted to set the `match_type` for each match during this process.
2.  **(Optional) Update Match Types:** If needed, correct `match_type` for existing matches using `stats_db_processor.py --update-match-types`.
3.  **Fix Pickup/Ranked Team IDs:** Run `fix_pickup_team_ids.py` to set `player_stats.team_id` to NULL for players in `pickup` and `ranked` matches. This is **required** before generating player ELO ladders.
4.  **Generate ELO Ladders:** Run `elo_ladder.py` with appropriate `--match-type` arguments.

## Match Types

Each match in the database has a `match_type` field:
- `team` - Organized matches between established teams.
- `pickup` - Custom pickup games where players are not necessarily representing established teams.
- `ranked` - Ranked queue matches where players queue individually.

**Setting Match Type:** When processing new match JSON files with `python -m stats_reader.stats_db_processor --input <dir>`, you will be prompted interactively to set the `match_type` for each match.

## Updating Existing Match Types

To update match types for matches already in the database, run:

```
python -m stats_reader.stats_db_processor --update-match-types
```

This provides options to set all matches to 'team', update by season, or update manually.

## Preparing Data for Player ELO (Important!)

The Player ELO calculation (`pickup` and `ranked` types) requires that the `team_id` field in the `player_stats` table is set to `NULL` for players participating in those match types.

However, the standard data processing assigns the match's team ID to player stats initially. Therefore, **before generating player ELO ladders**, you must run the following script:

```
python -m stats_reader.fix_pickup_team_ids --db your_database_name.db
```

This script will find player stats records associated with `pickup` or `ranked` matches that have a non-NULL `team_id` and update them to `NULL` after confirmation. Run this after processing your match data and before running `elo_ladder.py` for `pickup` or `ranked` types.

## Generating ELO Ladders

The ELO ladder generation creates multiple ladder files based on the specified `--match-type` (or all if none is specified):

- `elo_ladder_team.json` - Team ELO ratings for 'team' matches.
- `pickup_player_elo_ladder.json` - Individual player ELO ratings from 'pickup' matches.
- `ranked_player_elo_ladder.json` - Individual player ELO ratings from 'ranked' matches.
- `elo_ladder.json` - Combined team ladder with all matches (for backward compatibility).
- Associated `_history.json` files are also generated for each ladder.

To generate all ladders (after running `fix_pickup_team_ids.py` if needed):

```
python -m stats_reader.elo_ladder
```

To generate ladders for specific match types only:

```
python -m stats_reader.elo_ladder --match-type team     # Only team ladder
python -m stats_reader.elo_ladder --match-type pickup   # Only pickup player ladder (run fix_pickup_team_ids first!)
python -m stats_reader.elo_ladder --match-type ranked   # Only ranked player ladder (run fix_pickup_team_ids first!)
```

## Implementation Details

- **Team ELO (`team`)**: Calculated only from matches with `match_type = 'team'`, based on the ELO ratings of the competing teams.
- **Player ELO (`pickup`, `ranked`)**: Calculated from individual player performance in matches with `match_type = 'pickup'` or `match_type = 'ranked'`, **after** `player_stats.team_id` has been set to NULL for these matches using `fix_pickup_team_ids.py`. The calculation uses the average ELO of the players on each side of the match to determine expected outcomes and update individual player ratings.
