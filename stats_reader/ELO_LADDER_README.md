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
- **Match Order**: Matches are processed chronologically based on their `match_date`. If multiple matches share the exact same timestamp, they are processed in ascending order of their unique match `id` (the primary key). This typically results in a FIFO (First-In, First-Out) order based on when the matches were added to the database. For the most predictable ELO history, providing unique timestamps (even if estimated) is recommended when possible.

## Detailed Pickup/Ranked ELO Calculation

The player-based ELO calculation for pickup and ranked matches follows a specific process that you can manually verify if needed. Here's how it works in detail:

### Initial Setup
- All players start with a base ELO rating (default: 1000)
- The K-factor (default: 32) determines how much ratings change after each match

### Calculation Process for Each Match

1. **Match Processing Order**
   - Matches are processed strictly in chronological order by match_date
   - If multiple matches have the same timestamp, they're processed by match ID (lower IDs first)

2. **Team Average ELO Calculation**
   - For each match, the system calculates the average ELO of all players on each side:
     ```
     imperial_avg_elo = sum(imperial_player_ratings) / number_of_imperial_players
     rebel_avg_elo = sum(rebel_player_ratings) / number_of_rebel_players
     ```

3. **Expected Outcome Calculation**
   - The expected win probability is calculated using the standard ELO formula:
     ```
     imperial_expected = 1 / (1 + 10^((rebel_avg_elo - imperial_avg_elo) / 400))
     rebel_expected = 1 - imperial_expected
     ```

4. **Actual Outcome Determination**
   - Based on the match result:
     - Imperial win: imperial_actual = 1.0, rebel_actual = 0.0
     - Rebel win: imperial_actual = 0.0, rebel_actual = 1.0

5. **Rating Update Calculation**
   - Each player's rating is updated based on their team's performance:
     ```
     new_rating = old_rating + k_factor * (actual_outcome - expected_outcome)
     ```
   - All players on the same team receive the same adjustment to their ratings

6. **Storage and Progress**
   - The updated ratings are stored in memory and used for the next match
   - The history of rating changes is saved to the appropriate `*_player_elo_history.json` file
   - The final ratings are saved to the `*_player_elo_ladder.json` file

### Example Calculation

Here's an example calculation for a match between 5 Imperial players and 5 Rebel players:

**Initial Ratings:**
- Imperial players: [1100, 1050, 1000, 950, 900]
- Rebel players: [1200, 1150, 1100, 1050, 1000]
- K-factor: 32

**Step 1: Calculate Team Averages**
- Imperial average: (1100 + 1050 + 1000 + 950 + 900) / 5 = 1000
- Rebel average: (1200 + 1150 + 1100 + 1050 + 1000) / 5 = 1100

**Step 2: Calculate Expected Outcomes**
- Imperial expected: 1 / (1 + 10^((1100 - 1000) / 400)) = 0.36 (36% chance of winning)
- Rebel expected: 1 - 0.36 = 0.64 (64% chance of winning)

**Step 3: Actual Outcome (Let's say Imperial wins)**
- Imperial actual: 1.0
- Rebel actual: 0.0

**Step 4: Update Each Player's Rating**
- For each Imperial player:
  - Rating change: 32 * (1.0 - 0.36) = +20.48 points
- For each Rebel player:
  - Rating change: 32 * (0.0 - 0.64) = -20.48 points

**Step 5: New Ratings**
- Imperial players: [1120.48, 1070.48, 1020.48, 970.48, 920.48]
- Rebel players: [1179.52, 1129.52, 1079.52, 1029.52, 979.52]

### Important Notes About Rating Storage

1. The player ELO ratings are **not** stored in the database itself
2. Ratings are maintained in memory during processing and saved to JSON files
3. When you run the ladder generation script, it recalculates all ratings from scratch
4. This allows for "what-if" scenarios by adjusting parameters like the K-factor

To verify calculations, you can examine the `*_player_elo_history.json` file, which contains the detailed history of each player's rating changes over time.
