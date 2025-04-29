"""
Role-specific ELO ladder generator for Star Wars Squadrons pickup and ranked matches

This module calculates separate ELO ratings for players based on their role (Flex, Support, Farmer)
while still using the general ELO ratings for team average calculations.
"""
import os
import sys
import json
import sqlite3
import argparse
from datetime import datetime

# Import shared ELO calculation functions from the player_elo_ladder module
from stats_reader.player_elo_ladder import calculate_expected_outcome, calculate_new_rating

def generate_role_specific_elo(db_path, output_dir="elo_reports_pickup", starting_elo=1000, k_factor=32, match_type="pickup"):
    """
    Generate role-specific ELO ladders for players based on their roles
    
    Args:
        db_path (str): Path to the SQLite database
        output_dir (str): Directory to save the ELO ladder reports
        starting_elo (int): Starting ELO rating for new players
        k_factor (int): K-factor for ELO calculation
        match_type (str): Type of matches to include ('pickup' or 'ranked')
        
    Returns:
        dict: Dictionary containing ladders for each role and combined ladder
    """
    # Ensure output directory exists
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Connect to the database
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row  # Enable row factory for named columns
    cursor = conn.cursor()
    
    # Query pickup/ranked matches ordered by date
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
    print(f"\nLooking for {match_type} matches to generate role-specific ELO ladders")
    print(f"Found {len(matches)} matches of type '{match_type}'")
    
    # Initialize ELO ratings for all players
    general_elo_ratings = {}         # Used for team average calculation
    flex_elo_ratings = {}            # Flex role specific ratings
    support_elo_ratings = {}         # Support role specific ratings
    farmer_elo_ratings = {}          # Farmer role specific ratings
    
    # Query all players to ensure all have an initial rating
    cursor.execute("SELECT id, name, player_hash FROM players")
    players = [dict(row) for row in cursor.fetchall()]
    
    for player in players:
        player_id = player['id']
        general_elo_ratings[player_id] = starting_elo
        flex_elo_ratings[player_id] = starting_elo
        support_elo_ratings[player_id] = starting_elo
        farmer_elo_ratings[player_id] = starting_elo
    
    # Initialize ELO history for each role
    general_elo_history = []
    flex_elo_history = []
    support_elo_history = []
    farmer_elo_history = []
    
    # Process matches and update ELO ratings
    for match in matches:
        match_id = match['id']
        
        # Get imperial players
        cursor.execute("""
        SELECT player_id, player_name, player_hash, role
        FROM player_stats
        WHERE match_id = ? AND faction = 'IMPERIAL'
        """, (match_id,))
        
        imperial_players = [dict(row) for row in cursor.fetchall()]
        
        # Get rebel players
        cursor.execute("""
        SELECT player_id, player_name, player_hash, role
        FROM player_stats
        WHERE match_id = ? AND faction = 'REBEL'
        """, (match_id,))
        
        rebel_players = [dict(row) for row in cursor.fetchall()]
        
        # Skip matches with no players on either side
        if not imperial_players or not rebel_players:
            print(f"Skipping match ID {match_id} - missing players on one or both sides")
            continue
        
        # Calculate average ELO for each team using GENERAL ELO RATINGS
        imperial_elo_sum = 0
        rebel_elo_sum = 0
        
        for player in imperial_players:
            player_id = player['player_id']
            if player_id not in general_elo_ratings:
                general_elo_ratings[player_id] = starting_elo
            imperial_elo_sum += general_elo_ratings[player_id]
        
        for player in rebel_players:
            player_id = player['player_id']
            if player_id not in general_elo_ratings:
                general_elo_ratings[player_id] = starting_elo
            rebel_elo_sum += general_elo_ratings[player_id]
        
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
        
        # Update general ELO ratings and record history (for reference only)
        imperial_general_history = []
        rebel_general_history = []
        
        for player in imperial_players:
            player_id = player['player_id']
            old_rating = general_elo_ratings[player_id]
            new_rating = calculate_new_rating(old_rating, imperial_expected, imperial_actual, k_factor)
            general_elo_ratings[player_id] = new_rating
            imperial_general_history.append({
                'player_id': player_id,
                'player_name': player['player_name'],
                'role': player['role'],
                'old_rating': old_rating,
                'new_rating': new_rating,
                'rating_change': new_rating - old_rating
            })
        
        for player in rebel_players:
            player_id = player['player_id']
            old_rating = general_elo_ratings[player_id]
            new_rating = calculate_new_rating(old_rating, rebel_expected, rebel_actual, k_factor)
            general_elo_ratings[player_id] = new_rating
            rebel_general_history.append({
                'player_id': player_id,
                'player_name': player['player_name'],
                'role': player['role'],
                'old_rating': old_rating,
                'new_rating': new_rating,
                'rating_change': new_rating - old_rating
            })
        
        # Record general ELO history
        general_elo_history.append({
            'match_id': match_id,
            'match_date': match['match_date'],
            'season': match['season'],
            'imperial_players': imperial_general_history,
            'rebel_players': rebel_general_history,
            'winner': match['winner'],
            'imperial_avg_elo': imperial_avg_elo,
            'rebel_avg_elo': rebel_avg_elo
        })
        
        # Process role-specific ELO updates
        
        # 1. Update Flex ELO ratings
        imperial_flex_history = []
        rebel_flex_history = []
        
        for player in imperial_players:
            player_id = player['player_id']
            player_role = player['role']
            
            # Only update flex ELO if this player has the Flex role
            if player_role == 'Flex':
                old_rating = flex_elo_ratings[player_id]
                new_rating = calculate_new_rating(old_rating, imperial_expected, imperial_actual, k_factor)
                flex_elo_ratings[player_id] = new_rating
                imperial_flex_history.append({
                    'player_id': player_id,
                    'player_name': player['player_name'],
                    'role': player_role,
                    'old_rating': old_rating,
                    'new_rating': new_rating,
                    'rating_change': new_rating - old_rating
                })
        
        for player in rebel_players:
            player_id = player['player_id']
            player_role = player['role']
            
            # Only update flex ELO if this player has the Flex role
            if player_role == 'Flex':
                old_rating = flex_elo_ratings[player_id]
                new_rating = calculate_new_rating(old_rating, rebel_expected, rebel_actual, k_factor)
                flex_elo_ratings[player_id] = new_rating
                rebel_flex_history.append({
                    'player_id': player_id,
                    'player_name': player['player_name'],
                    'role': player_role,
                    'old_rating': old_rating,
                    'new_rating': new_rating,
                    'rating_change': new_rating - old_rating
                })
        
        # Record flex ELO history if any player's Flex rating changed
        if imperial_flex_history or rebel_flex_history:
            flex_elo_history.append({
                'match_id': match_id,
                'match_date': match['match_date'],
                'season': match['season'],
                'imperial_players': imperial_flex_history,
                'rebel_players': rebel_flex_history,
                'winner': match['winner'],
                'imperial_avg_elo': imperial_avg_elo,  # Still use general ELO for team average
                'rebel_avg_elo': rebel_avg_elo         # Still use general ELO for team average
            })
        
        # 2. Update Support ELO ratings
        imperial_support_history = []
        rebel_support_history = []
        
        for player in imperial_players:
            player_id = player['player_id']
            player_role = player['role']
            
            # Only update support ELO if this player has the Support role
            if player_role == 'Support':
                old_rating = support_elo_ratings[player_id]
                new_rating = calculate_new_rating(old_rating, imperial_expected, imperial_actual, k_factor)
                support_elo_ratings[player_id] = new_rating
                imperial_support_history.append({
                    'player_id': player_id,
                    'player_name': player['player_name'],
                    'role': player_role,
                    'old_rating': old_rating,
                    'new_rating': new_rating,
                    'rating_change': new_rating - old_rating
                })
        
        for player in rebel_players:
            player_id = player['player_id']
            player_role = player['role']
            
            # Only update support ELO if this player has the Support role
            if player_role == 'Support':
                old_rating = support_elo_ratings[player_id]
                new_rating = calculate_new_rating(old_rating, rebel_expected, rebel_actual, k_factor)
                support_elo_ratings[player_id] = new_rating
                rebel_support_history.append({
                    'player_id': player_id,
                    'player_name': player['player_name'],
                    'role': player_role,
                    'old_rating': old_rating,
                    'new_rating': new_rating,
                    'rating_change': new_rating - old_rating
                })
        
        # Record support ELO history if any player's Support rating changed
        if imperial_support_history or rebel_support_history:
            support_elo_history.append({
                'match_id': match_id,
                'match_date': match['match_date'],
                'season': match['season'],
                'imperial_players': imperial_support_history,
                'rebel_players': rebel_support_history,
                'winner': match['winner'],
                'imperial_avg_elo': imperial_avg_elo,  # Still use general ELO for team average
                'rebel_avg_elo': rebel_avg_elo         # Still use general ELO for team average
            })
        
        # 3. Update Farmer ELO ratings
        imperial_farmer_history = []
        rebel_farmer_history = []
        
        for player in imperial_players:
            player_id = player['player_id']
            player_role = player['role']
            
            # Only update farmer ELO if this player has the Farmer role
            if player_role == 'Farmer':
                old_rating = farmer_elo_ratings[player_id]
                new_rating = calculate_new_rating(old_rating, imperial_expected, imperial_actual, k_factor)
                farmer_elo_ratings[player_id] = new_rating
                imperial_farmer_history.append({
                    'player_id': player_id,
                    'player_name': player['player_name'],
                    'role': player_role,
                    'old_rating': old_rating,
                    'new_rating': new_rating,
                    'rating_change': new_rating - old_rating
                })
        
        for player in rebel_players:
            player_id = player['player_id']
            player_role = player['role']
            
            # Only update farmer ELO if this player has the Farmer role
            if player_role == 'Farmer':
                old_rating = farmer_elo_ratings[player_id]
                new_rating = calculate_new_rating(old_rating, rebel_expected, rebel_actual, k_factor)
                farmer_elo_ratings[player_id] = new_rating
                rebel_farmer_history.append({
                    'player_id': player_id,
                    'player_name': player['player_name'],
                    'role': player_role,
                    'old_rating': old_rating,
                    'new_rating': new_rating,
                    'rating_change': new_rating - old_rating
                })
        
        # Record farmer ELO history if any player's Farmer rating changed
        if imperial_farmer_history or rebel_farmer_history:
            farmer_elo_history.append({
                'match_id': match_id,
                'match_date': match['match_date'],
                'season': match['season'],
                'imperial_players': imperial_farmer_history,
                'rebel_players': rebel_farmer_history,
                'winner': match['winner'],
                'imperial_avg_elo': imperial_avg_elo,  # Still use general ELO for team average
                'rebel_avg_elo': rebel_avg_elo         # Still use general ELO for team average
            })
    
    # Build the role-specific ladders
    general_ladder = []
    flex_ladder = []
    support_ladder = []
    farmer_ladder = []
    
    for player in players:
        player_id = player['id']
        
        # Query to check if this player has played any pickup/ranked matches
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
        
        # Only include players who have played pickup/ranked matches
        if matches_played > 0:
            # Get the player's most common role
            cursor.execute("""
            SELECT 
                ps.role,
                COUNT(*) as role_count
            FROM player_stats ps
            JOIN matches m ON ps.match_id = m.id
            WHERE ps.player_id = ? AND m.match_type = ? AND ps.role IS NOT NULL
            GROUP BY ps.role
            ORDER BY role_count DESC
            LIMIT 1
            """, (player_id, match_type))
            
            role_row = cursor.fetchone()
            player_role = role_row['role'] if role_row else None
            
            # Make sure we don't divide by zero
            win_rate = 0
            if matches_played > 0:
                win_rate = round(matches_won / matches_played * 100, 1)
            
            # 1. Add to general ladder
            general_ladder.append({
                'player_id': player_id,
                'player_name': player['name'],
                'player_hash': player['player_hash'],
                'role': player_role,
                'elo_rating': round(general_elo_ratings[player_id]),
                'matches_played': matches_played,
                'matches_won': matches_won,
                'matches_lost': matches_lost,
                'win_rate': win_rate
            })
            
            # 2. Count matches played in each role
            cursor.execute("""
            SELECT 
                role,
                COUNT(*) as role_matches_played,
                SUM(CASE WHEN 
                        (ps.faction = 'IMPERIAL' AND m.winner = 'IMPERIAL') OR
                        (ps.faction = 'REBEL' AND m.winner = 'REBEL')
                    THEN 1 ELSE 0 END) as role_matches_won,
                SUM(CASE WHEN
                        (ps.faction = 'IMPERIAL' AND m.winner = 'REBEL') OR
                        (ps.faction = 'REBEL' AND m.winner = 'IMPERIAL')
                    THEN 1 ELSE 0 END) as role_matches_lost
            FROM player_stats ps
            JOIN matches m ON ps.match_id = m.id
            WHERE ps.player_id = ? AND m.match_type = ? AND m.winner IN ('IMPERIAL', 'REBEL')
            GROUP BY ps.role
            """, (player_id, match_type))
            
            role_stats = [dict(row) for row in cursor.fetchall()]
            
            # 3. Add to role-specific ladders
            for role_stat in role_stats:
                role = role_stat['role']
                role_matches_played = role_stat['role_matches_played'] or 0
                role_matches_won = role_stat['role_matches_won'] or 0
                role_matches_lost = role_stat['role_matches_lost'] or 0
                
                # Calculate win rate for this role
                role_win_rate = 0
                if role_matches_played > 0:
                    role_win_rate = round(role_matches_won / role_matches_played * 100, 1)
                
                if role == 'Flex' and role_matches_played > 0:
                    flex_ladder.append({
                        'player_id': player_id,
                        'player_name': player['name'],
                        'player_hash': player['player_hash'],
                        'role': 'Flex',
                        'elo_rating': round(flex_elo_ratings[player_id]),
                        'matches_played': role_matches_played,
                        'matches_won': role_matches_won,
                        'matches_lost': role_matches_lost,
                        'win_rate': role_win_rate
                    })
                
                if role == 'Support' and role_matches_played > 0:
                    support_ladder.append({
                        'player_id': player_id,
                        'player_name': player['name'],
                        'player_hash': player['player_hash'],
                        'role': 'Support',
                        'elo_rating': round(support_elo_ratings[player_id]),
                        'matches_played': role_matches_played,
                        'matches_won': role_matches_won,
                        'matches_lost': role_matches_lost,
                        'win_rate': role_win_rate
                    })
                
                if role == 'Farmer' and role_matches_played > 0:
                    farmer_ladder.append({
                        'player_id': player_id,
                        'player_name': player['name'],
                        'player_hash': player['player_hash'],
                        'role': 'Farmer',
                        'elo_rating': round(farmer_elo_ratings[player_id]),
                        'matches_played': role_matches_played,
                        'matches_won': role_matches_won,
                        'matches_lost': role_matches_lost,
                        'win_rate': role_win_rate
                    })
    
    # Sort ladders by ELO rating
    general_ladder.sort(key=lambda x: x['elo_rating'], reverse=True)
    flex_ladder.sort(key=lambda x: x['elo_rating'], reverse=True)
    support_ladder.sort(key=lambda x: x['elo_rating'], reverse=True)
    farmer_ladder.sort(key=lambda x: x['elo_rating'], reverse=True)
    
    # Add rank to each player
    for i, player in enumerate(general_ladder):
        player['rank'] = i + 1
    
    for i, player in enumerate(flex_ladder):
        player['rank'] = i + 1
    
    for i, player in enumerate(support_ladder):
        player['rank'] = i + 1
    
    for i, player in enumerate(farmer_ladder):
        player['rank'] = i + 1
    
    # Save ladders to files
    general_ladder_filename = f"{match_type}_player_elo_ladder.json"
    flex_ladder_filename = f"{match_type}_flex_elo_ladder.json"
    support_ladder_filename = f"{match_type}_support_elo_ladder.json"
    farmer_ladder_filename = f"{match_type}_farmer_elo_ladder.json"
    
    with open(os.path.join(output_dir, general_ladder_filename), "w") as f:
        json.dump(general_ladder, f, indent=2)
    
    with open(os.path.join(output_dir, flex_ladder_filename), "w") as f:
        json.dump(flex_ladder, f, indent=2)
    
    with open(os.path.join(output_dir, support_ladder_filename), "w") as f:
        json.dump(support_ladder, f, indent=2)
    
    with open(os.path.join(output_dir, farmer_ladder_filename), "w") as f:
        json.dump(farmer_ladder, f, indent=2)
    
    # Save history to files
    general_history_filename = f"{match_type}_player_elo_history.json"
    flex_history_filename = f"{match_type}_flex_elo_history.json"
    support_history_filename = f"{match_type}_support_elo_history.json"
    farmer_history_filename = f"{match_type}_farmer_elo_history.json"
    
    with open(os.path.join(output_dir, general_history_filename), "w") as f:
        json.dump(general_elo_history, f, indent=2)
    
    with open(os.path.join(output_dir, flex_history_filename), "w") as f:
        json.dump(flex_elo_history, f, indent=2)
    
    with open(os.path.join(output_dir, support_history_filename), "w") as f:
        json.dump(support_elo_history, f, indent=2)
    
    with open(os.path.join(output_dir, farmer_history_filename), "w") as f:
        json.dump(farmer_elo_history, f, indent=2)
    
    # Display summary
    print(f"\nRole-specific ELO ladders for {match_type} matches generated:")
    print(f"  - General: {len(general_ladder)} players")
    print(f"  - Flex: {len(flex_ladder)} players")
    print(f"  - Support: {len(support_ladder)} players")
    print(f"  - Farmer: {len(farmer_ladder)} players")
    print(f"Reports saved to {output_dir}:\n")
    
    # Display top players from each ladder
    print(f"Top 5 players in general {match_type} ELO ladder:")
    print("===========================================================")
    print(f"{'Rank':<5}{'Player':<25}{'Role':<10}{'ELO':<8}{'W-L':<10}{'Win %':<8}")
    print("-----------------------------------------------------------")
    for player in general_ladder[:5]:
        role_display = player['role'] if player['role'] else 'None'
        print(f"{player['rank']:<5}{player['player_name'][:24]:<25}{role_display:<10}{player['elo_rating']:<8}{player['matches_won']}-{player['matches_lost']:<10}{player['win_rate']}%")
    print("\n")
    
    print(f"Top 5 Flex players in {match_type} ELO ladder:")
    print("===========================================================")
    print(f"{'Rank':<5}{'Player':<25}{'Role':<10}{'ELO':<8}{'W-L':<10}{'Win %':<8}")
    print("-----------------------------------------------------------")
    for player in flex_ladder[:5]:
        role_display = player['role'] if player['role'] else 'None'
        print(f"{player['rank']:<5}{player['player_name'][:24]:<25}{role_display:<10}{player['elo_rating']:<8}{player['matches_won']}-{player['matches_lost']:<10}{player['win_rate']}%")
    print("\n")
    
    print(f"Top 5 Support players in {match_type} ELO ladder:")
    print("===========================================================")
    print(f"{'Rank':<5}{'Player':<25}{'Role':<10}{'ELO':<8}{'W-L':<10}{'Win %':<8}")
    print("-----------------------------------------------------------")
    for player in support_ladder[:5]:
        role_display = player['role'] if player['role'] else 'None'
        print(f"{player['rank']:<5}{player['player_name'][:24]:<25}{role_display:<10}{player['elo_rating']:<8}{player['matches_won']}-{player['matches_lost']:<10}{player['win_rate']}%")
    print("\n")
    
    print(f"Top 5 Farmer players in {match_type} ELO ladder:")
    print("===========================================================")
    print(f"{'Rank':<5}{'Player':<25}{'Role':<10}{'ELO':<8}{'W-L':<10}{'Win %':<8}")
    print("-----------------------------------------------------------")
    for player in farmer_ladder[:5]:
        role_display = player['role'] if player['role'] else 'None'
        print(f"{player['rank']:<5}{player['player_name'][:24]:<25}{role_display:<10}{player['elo_rating']:<8}{player['matches_won']}-{player['matches_lost']:<10}{player['win_rate']}%")
    
    conn.close()
    
    # Return all the ladders for easy reference
    return {
        'general': general_ladder,
        'flex': flex_ladder,
        'support': support_ladder,
        'farmer': farmer_ladder
    }


def main():
    """Command-line entry point for role-specific ELO ladder generation"""
    parser = argparse.ArgumentParser(description="Generate role-specific ELO ladders for players")
    
    parser.add_argument("--db", type=str, default="squadrons_stats.db",
                      help="SQLite database file path (default: squadrons_stats.db)")
    parser.add_argument("--output", type=str, default="elo_reports_pickup",
                      help="Directory for ELO ladder reports (default: elo_reports_pickup)")
    parser.add_argument("--starting-elo", type=int, default=1000,
                      help="Starting ELO rating for new players (default: 1000)")
    parser.add_argument("--k-factor", type=int, default=32,
                      help="K-factor for ELO calculation (default: 32)")
    parser.add_argument("--match-type", type=str, choices=["pickup", "ranked", "all"], default="all",
                      help="Generate ELO ladder only for a specific match type (default: all)")
    
    args = parser.parse_args()
    
    # Check that database exists
    if not os.path.exists(args.db):
        print(f"Error: Database file not found: {args.db}")
        print("Please run the stats_db_processor.py script first to generate the database.")
        sys.exit(1)
    
    if args.match_type == "pickup":
        # Generate pickup player ELO ladder
        generate_role_specific_elo(args.db, args.output, args.starting_elo, args.k_factor, "pickup")
    elif args.match_type == "ranked":
        # Generate ranked player ELO ladder
        generate_role_specific_elo(args.db, args.output, args.starting_elo, args.k_factor, "ranked")
    elif args.match_type == "all":
        # Generate both pickup and ranked player ELO ladders
        print("\nGenerating Pickup Player Role-Specific ELO ladders...")
        generate_role_specific_elo(args.db, args.output, args.starting_elo, args.k_factor, "pickup")
        print("\nGenerating Ranked Player Role-Specific ELO ladders...")
        generate_role_specific_elo(args.db, args.output, args.starting_elo, args.k_factor, "ranked")


if __name__ == "__main__":
    main()