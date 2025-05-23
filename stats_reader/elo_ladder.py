"""
ELO ladder generator for Star Wars Squadrons teams
"""
import os
import sys
import json
import sqlite3
import argparse
from datetime import datetime

def calculate_expected_outcome(rating_a, rating_b):
    """
    Calculate the expected outcome (probability of winning) for team A
    
    Args:
        rating_a (float): ELO rating of team A
        rating_b (float): ELO rating of team B
        
    Returns:
        float: Expected outcome (probability of team A winning)
    """
    return 1.0 / (1.0 + 10 ** ((rating_b - rating_a) / 400))

def calculate_new_rating(rating, expected_outcome, actual_outcome, k_factor):
    """
    Calculate the new ELO rating after a match
    
    Args:
        rating (float): Current ELO rating
        expected_outcome (float): Expected outcome (probability of winning)
        actual_outcome (float): Actual outcome (1=win, 0.5=draw, 0=loss)
        k_factor (int): K-factor for ELO calculation
        
    Returns:
        float: New ELO rating
    """
    return rating + k_factor * (actual_outcome - expected_outcome)

def generate_player_elo_ladder(db_path, output_dir="stats_reports", starting_elo=1000, k_factor=32, match_type="pickup", 
                          ladder_filename="player_elo_ladder.json", history_filename="player_elo_history.json"):
    """
    Generate an ELO ladder for individual players from pickup matches
    
    Args:
        db_path (str): Path to the SQLite database
        output_dir (str): Directory to save the ELO ladder reports
        starting_elo (int): Starting ELO rating for new players
        k_factor (int): K-factor for ELO calculation
        match_type (str): Type of matches to include ('pickup' or 'ranked')
        ladder_filename (str): Filename for saving the ladder
        history_filename (str): Filename for saving the history
        
    Returns:
        tuple: (elo_ladder, elo_history) containing the final ladder and history
    """
    # Ensure output directory exists
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Connect to the database
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row  # Enable row factory for named columns
    cursor = conn.cursor()
    
    # Query pickup matches ordered by date
    cursor.execute("""
    SELECT m.id, m.match_date, m.winner,
           s.name as season
    FROM matches m
    JOIN seasons s ON m.season_id = s.id
    WHERE m.winner IN ('IMPERIAL', 'REBEL')
    AND m.match_type = ?
    ORDER BY m.match_date, m.id
    """, (match_type,))
    
    matches = [dict(row) for row in cursor.fetchall()]
    
    # Debug info
    print(f"\nLooking for matches with match_type = '{match_type}'")
    print(f"Found {len(matches)} matches of type '{match_type}'")
    
    # For player ELO, we need to ensure we have players in the matches
    cursor.execute("""
    SELECT COUNT(*) as count
    FROM player_stats ps
    JOIN matches m ON ps.match_id = m.id
    WHERE m.match_type = ?
    """, (match_type,))
    
    player_count = cursor.fetchone()['count']
    print(f"Found {player_count} player entries in '{match_type}' matches")
    
    # For pickup/ranked matches, ensure we're processing players without team IDs
    if match_type in ['pickup', 'ranked']:
        cursor.execute("""
        SELECT COUNT(*) as count
        FROM player_stats ps
        JOIN matches m ON ps.match_id = m.id
        WHERE m.match_type = ? AND ps.team_id IS NULL
        """, (match_type,))
        
        null_team_count = cursor.fetchone()['count']
        print(f"Found {null_team_count} player entries in '{match_type}' matches with NULL team_id")
        
        if null_team_count == 0 and player_count > 0:
            print("WARNING: Pickup/ranked matches should have team_id set to NULL for player stats")
            print("         Run fix_pickup_team_ids.py to correct this issue")
    
    # Initialize ELO ratings for players
    elo_ratings = {}
    
    # Query all players to ensure all have an initial rating
    cursor.execute("SELECT id, name, player_hash FROM players")
    players = [dict(row) for row in cursor.fetchall()]
    
    for player in players:
        elo_ratings[player['id']] = starting_elo
    
    # Process matches and update ELO ratings
    elo_history = []
    
    for match in matches:
        match_id = match['id']
        
        # Get imperial players
        cursor.execute("""
        SELECT player_id, player_name, player_hash
        FROM player_stats
        WHERE match_id = ? AND faction = 'IMPERIAL'
        """, (match_id,))
        
        imperial_players = [dict(row) for row in cursor.fetchall()]
        
        # Get rebel players
        cursor.execute("""
        SELECT player_id, player_name, player_hash
        FROM player_stats
        WHERE match_id = ? AND faction = 'REBEL'
        """, (match_id,))
        
        rebel_players = [dict(row) for row in cursor.fetchall()]
        
        # Skip matches with no players on either side
        if not imperial_players or not rebel_players:
            continue
        
        # Calculate average ELO for each team
        imperial_elo_sum = 0
        rebel_elo_sum = 0
        
        for player in imperial_players:
            player_id = player['player_id']
            if player_id not in elo_ratings:
                elo_ratings[player_id] = starting_elo
            imperial_elo_sum += elo_ratings[player_id]
        
        for player in rebel_players:
            player_id = player['player_id']
            if player_id not in elo_ratings:
                elo_ratings[player_id] = starting_elo
            rebel_elo_sum += elo_ratings[player_id]
        
        imperial_avg_elo = imperial_elo_sum / len(imperial_players)
        rebel_avg_elo = rebel_elo_sum / len(rebel_players)
        
        # Calculate expected outcomes
        imperial_expected = calculate_expected_outcome(imperial_avg_elo, rebel_avg_elo)
        rebel_expected = 1.0 - imperial_expected
        
        # Determine actual outcomes
        if match['winner'] == 'IMPERIAL':
            imperial_actual = 1.0
            rebel_actual = 0.0
        else:  # REBEL
            imperial_actual = 0.0
            rebel_actual = 1.0
        
        # Record pre-update ratings for history
        imperial_players_history = []
        rebel_players_history = []
        
        # Update imperial player ratings
        for player in imperial_players:
            player_id = player['player_id']
            old_rating = elo_ratings[player_id]
            new_rating = calculate_new_rating(old_rating, imperial_expected, imperial_actual, k_factor)
            elo_ratings[player_id] = new_rating
            imperial_players_history.append({
                'player_id': player_id,
                'player_name': player['player_name'],
                'old_rating': old_rating,
                'new_rating': new_rating,
                'rating_change': new_rating - old_rating
            })
        
        # Update rebel player ratings
        for player in rebel_players:
            player_id = player['player_id']
            old_rating = elo_ratings[player_id]
            new_rating = calculate_new_rating(old_rating, rebel_expected, rebel_actual, k_factor)
            elo_ratings[player_id] = new_rating
            rebel_players_history.append({
                'player_id': player_id,
                'player_name': player['player_name'],
                'old_rating': old_rating,
                'new_rating': new_rating,
                'rating_change': new_rating - old_rating
            })
        
        # Record history
        elo_history.append({
            'match_id': match_id,
            'match_date': match['match_date'],
            'season': match['season'],
            'imperial_players': imperial_players_history,
            'rebel_players': rebel_players_history,
            'winner': match['winner']
        })
    
    # Build the final ladder
    ladder = []
    for player in players:
        player_id = player['id']
        if player_id in elo_ratings:
            # Count matches played and won for this player
            cursor.execute("""
            SELECT 
                COUNT(DISTINCT ps.match_id) as matches_played,
                SUM(CASE WHEN 
                        (ps.faction = 'IMPERIAL' AND m.winner = 'IMPERIAL') OR
                        (ps.faction = 'REBEL' AND m.winner = 'REBEL')
                    THEN 1 ELSE 0 END) as matches_won,
                SUM(CASE WHEN
                        (ps.faction = 'IMPERIAL' AND m.winner = 'REBEL') OR
                        (ps.faction = 'REBEL' AND m.winner = 'IMPERIAL')
                    THEN 1 ELSE 0 END) as matches_lost
            FROM player_stats ps
            JOIN matches m ON ps.match_id = m.id
            WHERE ps.player_id = ? AND m.match_type = ? AND m.winner IN ('IMPERIAL', 'REBEL')
            """, (player_id, match_type))
            
            stats = dict(cursor.fetchone())
            
            # Fix for win rate calculation
            matches_played = stats['matches_played'] or 0
            matches_won = stats['matches_won'] or 0
            matches_lost = stats['matches_lost'] or 0
            
            # Only include players who have actually played pickup matches
            if matches_played > 0:
                # Make sure we don't divide by zero
                win_rate = 0
                if matches_played > 0:
                    win_rate = round(matches_won / matches_played * 100, 1)
                
                ladder.append({
                    'player_id': player_id,
                    'player_name': player['name'],
                    'player_hash': player['player_hash'],
                    'elo_rating': round(elo_ratings[player_id]),
                    'matches_played': matches_played,
                    'matches_won': matches_won,
                    'matches_lost': matches_lost,
                    'win_rate': win_rate
                })
    
    # Sort ladder by ELO rating descending
    ladder.sort(key=lambda x: x['elo_rating'], reverse=True)
    
    # Add rank to each player
    for i, player in enumerate(ladder):
        player['rank'] = i + 1
    
    # Save ladder to file
    with open(os.path.join(output_dir, ladder_filename), "w") as f:
        json.dump(ladder, f, indent=2)
    
    # Save history to file
    with open(os.path.join(output_dir, history_filename), "w") as f:
        json.dump(elo_history, f, indent=2)
    
    # Display summary
    print(f"\nPlayer ELO ladder generated with {len(ladder)} players and {len(elo_history)} match updates")
    print(f"Reports saved to {output_dir}:")
    print(f"  - {ladder_filename}: Current ELO ratings for players in {match_type} matches")
    print(f"  - {history_filename}: Full history of ELO changes for each player\n")
    
    # Display top players with fixed formatting
    print(f"Top 10 players by ELO rating:")
    print("===========================================================")
    print(f"{'Rank':<5}{'Player':<20}{'ELO':<8}{'W-L':<10}{'Win %':<8}")
    print("-----------------------------------------------------------")
    for player in ladder[:10]:
        print(f"{player['rank']:<5}{player['player_name'][:19]:<20}{player['elo_rating']:<8}{player['matches_won']}-{player['matches_lost']:<10}{player['win_rate']}%")
    
    conn.close()
    return ladder, elo_history

def generate_elo_ladder(db_path, output_dir="stats_reports", starting_elo=1000, k_factor=32, match_type="team"):
    """
    Generate an ELO ladder from match data
    
    Args:
        db_path (str): Path to the SQLite database
        output_dir (str): Directory to save the ELO ladder reports
        starting_elo (int): Starting ELO rating for new teams
        k_factor (int): K-factor for ELO calculation
        
    Returns:
        tuple: (elo_ladder, elo_history) containing the final ladder and history
    """
    # Ensure output directory exists
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Connect to the database
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row  # Enable row factory for named columns
    cursor = conn.cursor()
    
    # Query matches of the specific type ordered by date
    cursor.execute("""
    SELECT m.id, m.match_date, m.winner,
           t_imp.id as imperial_team_id, t_imp.name as imperial_team_name,
           t_reb.id as rebel_team_id, t_reb.name as rebel_team_name,
           s.name as season
    FROM matches m
    JOIN teams t_imp ON m.imperial_team_id = t_imp.id
    JOIN teams t_reb ON m.rebel_team_id = t_reb.id
    JOIN seasons s ON m.season_id = s.id
    WHERE m.winner IN ('IMPERIAL', 'REBEL')
    AND m.match_type = ?
    ORDER BY m.match_date, m.id
    """, (match_type,))
    
    matches = [dict(row) for row in cursor.fetchall()]
    
    # Initialize ELO ratings for teams
    elo_ratings = {}
    
    # Query all teams to ensure all have an initial rating
    cursor.execute("SELECT id, name FROM teams")
    teams = [dict(row) for row in cursor.fetchall()]
    
    for team in teams:
        elo_ratings[team['id']] = starting_elo
    
    # Process matches and update ELO ratings
    elo_history = []
    
    for match in matches:
        imperial_id = match['imperial_team_id']
        rebel_id = match['rebel_team_id']
        imperial_name = match['imperial_team_name']
        rebel_name = match['rebel_team_name']
        
        # Ensure both teams have an ELO rating
        if imperial_id not in elo_ratings:
            elo_ratings[imperial_id] = starting_elo
        if rebel_id not in elo_ratings:
            elo_ratings[rebel_id] = starting_elo
        
        # Get current ratings
        imperial_rating = elo_ratings[imperial_id]
        rebel_rating = elo_ratings[rebel_id]
        
        # Calculate expected outcomes
        imperial_expected = calculate_expected_outcome(imperial_rating, rebel_rating)
        rebel_expected = 1.0 - imperial_expected
        
        # Determine actual outcomes
        if match['winner'] == 'IMPERIAL':
            imperial_actual = 1.0
            rebel_actual = 0.0
        else:  # REBEL
            imperial_actual = 0.0
            rebel_actual = 1.0
        
        # Calculate new ratings
        new_imperial_rating = calculate_new_rating(imperial_rating, imperial_expected, imperial_actual, k_factor)
        new_rebel_rating = calculate_new_rating(rebel_rating, rebel_expected, rebel_actual, k_factor)
        
        # Update ratings
        elo_ratings[imperial_id] = new_imperial_rating
        elo_ratings[rebel_id] = new_rebel_rating
        
        # Record history
        elo_history.append({
            'match_id': match['id'],
            'match_date': match['match_date'],
            'season': match['season'],
            'imperial': {
                'team_id': imperial_id,
                'team_name': imperial_name,
                'old_rating': imperial_rating,
                'new_rating': new_imperial_rating,
                'rating_change': new_imperial_rating - imperial_rating
            },
            'rebel': {
                'team_id': rebel_id,
                'team_name': rebel_name,
                'old_rating': rebel_rating,
                'new_rating': new_rebel_rating,
                'rating_change': new_rebel_rating - rebel_rating
            },
            'winner': match['winner']
        })
    
    # Build the final ladder
    ladder = []
    for team in teams:
        team_id = team['id']
        if team_id in elo_ratings:
            # Count matches played and won
            cursor.execute("""
            SELECT 
                COUNT(*) as matches_played,
                SUM(CASE WHEN 
                        (imperial_team_id = ? AND winner = 'IMPERIAL') OR
                        (rebel_team_id = ? AND winner = 'REBEL')
                    THEN 1 ELSE 0 END) as matches_won,
                SUM(CASE WHEN
                        (imperial_team_id = ? AND winner = 'REBEL') OR
                        (rebel_team_id = ? AND winner = 'IMPERIAL')
                    THEN 1 ELSE 0 END) as matches_lost
            FROM matches
            WHERE (imperial_team_id = ? OR rebel_team_id = ?) 
            AND winner IN ('IMPERIAL', 'REBEL')
            AND match_type = ?
            """, (team_id, team_id, team_id, team_id, team_id, team_id, match_type))
            
            stats = dict(cursor.fetchone())
            
            # Fix for win rate calculation
            matches_played = stats['matches_played'] or 0
            matches_won = stats['matches_won'] or 0
            matches_lost = stats['matches_lost'] or 0
            
            # Make sure we don't divide by zero
            win_rate = 0
            if matches_played > 0:
                win_rate = round(matches_won / matches_played * 100, 1)
            
            ladder.append({
                'team_id': team_id,
                'team_name': team['name'],
                'elo_rating': round(elo_ratings[team_id]),
                'matches_played': matches_played,
                'matches_won': matches_won,
                'matches_lost': matches_lost,
                'win_rate': win_rate
            })
    
    # Sort ladder by ELO rating descending
    ladder.sort(key=lambda x: x['elo_rating'], reverse=True)
    
    # Add rank to each team
    for i, team in enumerate(ladder):
        team['rank'] = i + 1
    
    # Save ladder to file with match type in filename
    ladder_filename = f"elo_ladder_{match_type}.json"
    with open(os.path.join(output_dir, ladder_filename), "w") as f:
        json.dump(ladder, f, indent=2)
    
    # Save history to file with match type in filename
    history_filename = f"elo_history_{match_type}.json"
    with open(os.path.join(output_dir, history_filename), "w") as f:
        json.dump(elo_history, f, indent=2)
    
    # Display summary
    print(f"\n{match_type.capitalize()} ELO ladder generated with {len(ladder)} teams and {len(elo_history)} match updates")
    print(f"Reports saved to {output_dir}:")
    print(f"  - {ladder_filename}: Current ELO ratings for all {match_type} teams")
    print(f"  - {history_filename}: Full history of ELO changes for each {match_type} match\n")
    
    # Display top teams with fixed formatting
    print(f"Top 10 {match_type} teams by ELO rating:")
    print("===========================================================")
    print(f"{'Rank':<5}{'Team':<20}{'ELO':<8}{'W-L':<10}{'Win %':<8}")
    print("-----------------------------------------------------------")
    for team in ladder[:10]:
        print(f"{team['rank']:<5}{team['team_name'][:19]:<20}{team['elo_rating']:<8}{team['matches_won']}-{team['matches_lost']:<10}{team['win_rate']}%")
    
    conn.close()
    return ladder, elo_history

def generate_combined_ladder(db_path, output_dir="stats_reports", starting_elo=1000, k_factor=32):
    """
    Generate a combined ELO ladder for all matches, for backward compatibility
    
    Args:
        db_path (str): Path to the SQLite database
        output_dir (str): Directory to save the ELO ladder reports
        starting_elo (int): Starting ELO rating for new teams
        k_factor (int): K-factor for ELO calculation
        
    Returns:
        tuple: (elo_ladder, elo_history) containing the final ladder and history
    """
    # Ensure output directory exists
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Connect to the database
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row  # Enable row factory for named columns
    cursor = conn.cursor()
    
    # Query all matches ordered by date
    cursor.execute("""
    SELECT m.id, m.match_date, m.winner,
           t_imp.id as imperial_team_id, t_imp.name as imperial_team_name,
           t_reb.id as rebel_team_id, t_reb.name as rebel_team_name,
           s.name as season
    FROM matches m
    JOIN teams t_imp ON m.imperial_team_id = t_imp.id
    JOIN teams t_reb ON m.rebel_team_id = t_reb.id
    JOIN seasons s ON m.season_id = s.id
    WHERE m.winner IN ('IMPERIAL', 'REBEL')
    ORDER BY m.match_date
    """)
    
    matches = [dict(row) for row in cursor.fetchall()]
    
    # Initialize ELO ratings for teams
    elo_ratings = {}
    
    # Query all teams to ensure all have an initial rating
    cursor.execute("SELECT id, name FROM teams")
    teams = [dict(row) for row in cursor.fetchall()]
    
    for team in teams:
        elo_ratings[team['id']] = starting_elo
    
    # Process matches and update ELO ratings
    elo_history = []
    
    for match in matches:
        imperial_id = match['imperial_team_id']
        rebel_id = match['rebel_team_id']
        imperial_name = match['imperial_team_name']
        rebel_name = match['rebel_team_name']
        
        # Ensure both teams have an ELO rating
        if imperial_id not in elo_ratings:
            elo_ratings[imperial_id] = starting_elo
        if rebel_id not in elo_ratings:
            elo_ratings[rebel_id] = starting_elo
        
        # Get current ratings
        imperial_rating = elo_ratings[imperial_id]
        rebel_rating = elo_ratings[rebel_id]
        
        # Calculate expected outcomes
        imperial_expected = calculate_expected_outcome(imperial_rating, rebel_rating)
        rebel_expected = 1.0 - imperial_expected
        
        # Determine actual outcomes
        if match['winner'] == 'IMPERIAL':
            imperial_actual = 1.0
            rebel_actual = 0.0
        else:  # REBEL
            imperial_actual = 0.0
            rebel_actual = 1.0
        
        # Calculate new ratings
        new_imperial_rating = calculate_new_rating(imperial_rating, imperial_expected, imperial_actual, k_factor)
        new_rebel_rating = calculate_new_rating(rebel_rating, rebel_expected, rebel_actual, k_factor)
        
        # Update ratings
        elo_ratings[imperial_id] = new_imperial_rating
        elo_ratings[rebel_id] = new_rebel_rating
        
        # Record history
        elo_history.append({
            'match_id': match['id'],
            'match_date': match['match_date'],
            'season': match['season'],
            'imperial': {
                'team_id': imperial_id,
                'team_name': imperial_name,
                'old_rating': imperial_rating,
                'new_rating': new_imperial_rating,
                'rating_change': new_imperial_rating - imperial_rating
            },
            'rebel': {
                'team_id': rebel_id,
                'team_name': rebel_name,
                'old_rating': rebel_rating,
                'new_rating': new_rebel_rating,
                'rating_change': new_rebel_rating - rebel_rating
            },
            'winner': match['winner']
        })
    
    # Build the final ladder
    ladder = []
    for team in teams:
        team_id = team['id']
        if team_id in elo_ratings:
            # Count matches played and won (all match types)
            cursor.execute("""
            SELECT 
                COUNT(*) as matches_played,
                SUM(CASE WHEN 
                        (imperial_team_id = ? AND winner = 'IMPERIAL') OR
                        (rebel_team_id = ? AND winner = 'REBEL')
                    THEN 1 ELSE 0 END) as matches_won,
                SUM(CASE WHEN
                        (imperial_team_id = ? AND winner = 'REBEL') OR
                        (rebel_team_id = ? AND winner = 'IMPERIAL')
                    THEN 1 ELSE 0 END) as matches_lost
            FROM matches
            WHERE (imperial_team_id = ? OR rebel_team_id = ?) AND winner IN ('IMPERIAL', 'REBEL')
            """, (team_id, team_id, team_id, team_id, team_id, team_id))
            
            stats = dict(cursor.fetchone())
            
            # Fix for win rate calculation
            matches_played = stats['matches_played'] or 0
            matches_won = stats['matches_won'] or 0
            matches_lost = stats['matches_lost'] or 0
            
            # Make sure we don't divide by zero
            win_rate = 0
            if matches_played > 0:
                win_rate = round(matches_won / matches_played * 100, 1)
            
            ladder.append({
                'team_id': team_id,
                'team_name': team['name'],
                'elo_rating': round(elo_ratings[team_id]),
                'matches_played': matches_played,
                'matches_won': matches_won,
                'matches_lost': matches_lost,
                'win_rate': win_rate
            })
    
    # Sort ladder by ELO rating descending
    ladder.sort(key=lambda x: x['elo_rating'], reverse=True)
    
    # Add rank to each team
    for i, team in enumerate(ladder):
        team['rank'] = i + 1
    
    # Save ladder to file (original filenames for backward compatibility)
    with open(os.path.join(output_dir, "elo_ladder.json"), "w") as f:
        json.dump(ladder, f, indent=2)
    
    # Save history to file (original filenames for backward compatibility)
    with open(os.path.join(output_dir, "elo_history.json"), "w") as f:
        json.dump(elo_history, f, indent=2)
    
    # Display summary
    print(f"\nCombined ELO ladder generated with {len(ladder)} teams and {len(elo_history)} match updates")
    print(f"Reports saved to {output_dir}:")
    print(f"  - elo_ladder.json: Current ELO ratings (all matches combined)")
    print(f"  - elo_history.json: Full history of ELO changes (all matches combined)\n")
    
    conn.close()
    return ladder, elo_history


def main():
    """Command-line entry point"""
    parser = argparse.ArgumentParser(description="Generate ELO ladder from Star Wars Squadrons match data")
    
    parser.add_argument("--db", type=str, default="squadrons_stats.db",
                      help="SQLite database file path (default: squadrons_stats.db)")
    parser.add_argument("--output", type=str, default="stats_reports",
                      help="Directory for ELO ladder reports (default: stats_reports)")
    parser.add_argument("--starting-elo", type=int, default=1000,
                      help="Starting ELO rating for new teams (default: 1000)")
    parser.add_argument("--k-factor", type=int, default=32,
                      help="K-factor for ELO calculation (default: 32)")
    parser.add_argument("--match-type", type=str, choices=["team", "pickup", "ranked", "all"], default="all",
                      help="Generate ELO ladder only for a specific match type (default: all)")
    
    args = parser.parse_args()
    
    # Check that database exists
    if not os.path.exists(args.db):
        print(f"Error: Database file not found: {args.db}")
        print("Please run the stats_db_processor.py script first to generate the database.")
        sys.exit(1)
    
    if args.match_type == "team":
        # Generate team ELO ladder
        generate_elo_ladder(args.db, args.output, args.starting_elo, args.k_factor, "team")
    elif args.match_type == "pickup":
        # Generate pickup player ELO ladder
        generate_player_elo_ladder(args.db, args.output, args.starting_elo, args.k_factor, "pickup",
                                 "pickup_player_elo_ladder.json", "pickup_player_elo_history.json")
    elif args.match_type == "ranked":
        # Generate ranked player ELO ladder
        generate_player_elo_ladder(args.db, args.output, args.starting_elo, args.k_factor, "ranked",
                                 "ranked_player_elo_ladder.json", "ranked_player_elo_history.json")
    elif args.match_type == "all":
        # Generate all ladders
        print("\nGenerating Team ELO ladder...")
        generate_elo_ladder(args.db, args.output, args.starting_elo, args.k_factor, "team")
        print("\nGenerating Pickup Player ELO ladder...")
        generate_player_elo_ladder(args.db, args.output, args.starting_elo, args.k_factor, "pickup", "pickup_player_elo_ladder.json", "pickup_player_elo_history.json")
        print("\nGenerating Ranked Player ELO ladder...")
        generate_player_elo_ladder(args.db, args.output, args.starting_elo, args.k_factor, "ranked", "ranked_player_elo_ladder.json", "ranked_player_elo_history.json")
        # Generate combined ladder for backward compatibility
        generate_combined_ladder(args.db, args.output, args.starting_elo, args.k_factor)

if __name__ == "__main__":
    main()
