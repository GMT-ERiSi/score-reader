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

def generate_elo_ladder(db_path, output_dir="stats_reports", starting_elo=1000, k_factor=32):
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
    
    # Save ladder to file
    with open(os.path.join(output_dir, "elo_ladder.json"), "w") as f:
        json.dump(ladder, f, indent=2)
    
    # Save history to file
    with open(os.path.join(output_dir, "elo_history.json"), "w") as f:
        json.dump(elo_history, f, indent=2)
    
    # Display summary
    print(f"\nELO ladder generated with {len(ladder)} teams and {len(elo_history)} match updates")
    print(f"Reports saved to {output_dir}:")
    print(f"  - elo_ladder.json: Current ELO ratings for all teams")
    print(f"  - elo_history.json: Full history of ELO changes for each match\n")
    
    # Display top teams with fixed formatting
    print("Top 10 teams by ELO rating:")
    print("===========================================================")
    print(f"{'Rank':<5}{'Team':<20}{'ELO':<8}{'W-L':<10}{'Win %':<8}")
    print("-----------------------------------------------------------")
    for team in ladder[:10]:
        print(f"{team['rank']:<5}{team['team_name'][:19]:<20}{team['elo_rating']:<8}{team['matches_won']}-{team['matches_lost']:<10}{team['win_rate']}%")
    
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
    
    args = parser.parse_args()
    
    # Check that database exists
    if not os.path.exists(args.db):
        print(f"Error: Database file not found: {args.db}")
        print("Please run the stats_db_processor.py script first to generate the database.")
        sys.exit(1)
    
    # Generate the ELO ladder
    generate_elo_ladder(args.db, args.output, args.starting_elo, args.k_factor)

if __name__ == "__main__":
    main()