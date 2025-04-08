# ELO Ladder System for Star Wars Squadrons

This system now supports multiple ELO ladders for different match types:

1. **Team ELO Ladder** - For organized team matches (match_type = 'team')
2. **Pickup ELO Ladder** - For custom pickup team matches (match_type = 'pickup')
3. **Pickup Player ELO Ladder** - For individual player rankings from custom pickup matches
4. **Ranked Player ELO Ladder** - For individual player rankings from ranked queue matches

## Match Types

Each match in the database now has a `match_type` field that can be:
- `team` - Organized matches between established teams
- `pickup` - Custom pickup games where players are not representing established teams
- `ranked` - Ranked queue matches where players queue individually

## Updating Existing Matches

To update match types for existing matches in the database, run:

```
python -m stats_reader.stats_db_processor --update-match-types
```

This will guide you through the process of setting match types for existing matches, with options to:
- Set all matches to 'team' type
- Update match types by season
- Manually update match types for individual matches

## Generating ELO Ladders

The ELO ladder generation creates multiple ladder files:

- `elo_ladder_team.json` - Team ELO ratings for organized team matches
- `elo_ladder_pickup.json` - Team ELO ratings for pickup matches
- `pickup_player_elo_ladder.json` - Individual player ELO ratings from custom pickup matches
- `ranked_player_elo_ladder.json` - Individual player ELO ratings from ranked queue matches
- `elo_ladder.json` - Combined ladder with all matches (for backward compatibility)

To generate all ladders, run:

```
python -m stats_reader.elo_ladder
```

You can also generate ladders for specific match types only:

```
python -m stats_reader.elo_ladder --match-type team     # Only team ladder
python -m stats_reader.elo_ladder --match-type pickup   # Only pickup ladders
python -m stats_reader.elo_ladder --match-type ranked   # Only ranked ladder
```

## Implementation Details

- Team ELO: Calculated only from matches with match_type = 'team'
- Pickup Team ELO: Calculated only from matches with match_type = 'pickup'
- Pickup Player ELO: Calculated from individual player performance in custom pickup matches
- Ranked Player ELO: Calculated from individual player performance in ranked queue matches

When processing new matches, you'll be prompted to specify the match type. Make sure to set it correctly based on whether it's an organized team match or a pickup game.
