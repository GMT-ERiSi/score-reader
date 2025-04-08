#!/usr/bin/env python3
"""
Check player and match data to debug ELO ladder issues
"""

import os
import sys
import sqlite3
import argparse

def check_match_player_data(db_path):
    """
    Analyze match data and player stats to identify issues
    
    Args:
        db_path (str): Path to the SQLite database
    """
    if not os.path.exists(db_path):
        print(f"Error: Database file not found: {db_path}")
        return False
        
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row  # Enable row factory for named columns
    cursor = conn.cursor()
    
    # Check match types
    cursor.execute("SELECT match_type, COUNT(*) FROM matches GROUP BY match_type")
    print("\nMatch Type Distribution:")
    print("-" * 40)
    match_types = cursor.fetchall()
    for row in match_types:
        print(f"{row[0]}: {row[1]} matches")
    
    # Check player stats per match type
    for match_type in [row[0] for row in match_types]:
        cursor.execute("""
        SELECT COUNT(*) as player_count
        FROM player_stats ps
        JOIN matches m ON ps.match_id = m.id
        WHERE m.match_type = ?
        """, (match_type,))
        
        player_count = cursor.fetchone()[0]
        print(f"\nPlayers in '{match_type}' matches: {player_count}")
        
        # Sample some players from this match type
        cursor.execute("""
        SELECT ps.player_id, ps.player_name, ps.faction, ps.team_id, t.name as team_name, m.id as match_id
        FROM player_stats ps
        JOIN matches m ON ps.match_id = m.id
        LEFT JOIN teams t ON ps.team_id = t.id
        WHERE m.match_type = ?
        LIMIT 5
        """, (match_type,))
        
        players = cursor.fetchall()
        print(f"Sample players in '{match_type}' matches:")
        for player in players:
            print(f"  {player['player_name']} ({player['faction']}) - Team: {player['team_name'] or 'None'} (ID: {player['team_id'] or 'None'})")
    
    # Check for team_id in pickup matches
    cursor.execute("""
    SELECT COUNT(*) as count
    FROM player_stats ps
    JOIN matches m ON ps.match_id = m.id
    WHERE m.match_type = 'pickup' AND ps.team_id IS NOT NULL
    """)
    
    pickup_with_team_id = cursor.fetchone()[0]
    print(f"\nPlayer stats in pickup matches with team_id NOT NULL: {pickup_with_team_id}")
    if pickup_with_team_id > 0:
        print("WARNING: Pickup matches should have team_id set to NULL for player stats")
    
    # Check for matches with no players
    cursor.execute("""
    SELECT m.id, m.match_date, m.match_type,
           t_imp.name as imperial_team, t_reb.name as rebel_team
    FROM matches m
    JOIN teams t_imp ON m.imperial_team_id = t_imp.id
    JOIN teams t_reb ON m.rebel_team_id = t_reb.id
    WHERE m.id NOT IN (SELECT DISTINCT match_id FROM player_stats)
    """)
    
    empty_matches = cursor.fetchall()
    if empty_matches:
        print("\nMatches with no player stats:")
        print("-" * 40)
        for match in empty_matches:
            print(f"Match ID: {match['id']}, Type: {match['match_type']}, Teams: {match['imperial_team']} vs {match['rebel_team']}")
    else:
        print("\nAll matches have player stats - good!")
    
    # Check for team_id mismatches
    cursor.execute("""
    SELECT ps.id, ps.player_name, ps.faction, ps.team_id, 
           m.id as match_id, m.match_type,
           CASE 
               WHEN ps.faction = 'IMPERIAL' THEN m.imperial_team_id
               WHEN ps.faction = 'REBEL' THEN m.rebel_team_id
           END as expected_team_id,
           t1.name as player_team, 
           CASE 
               WHEN ps.faction = 'IMPERIAL' THEN t2.name
               WHEN ps.faction = 'REBEL' THEN t3.name
           END as match_team
    FROM player_stats ps
    JOIN matches m ON ps.match_id = m.id
    LEFT JOIN teams t1 ON ps.team_id = t1.id
    LEFT JOIN teams t2 ON m.imperial_team_id = t2.id
    LEFT JOIN teams t3 ON m.rebel_team_id = t3.id
    WHERE ps.team_id IS NOT NULL AND ps.team_id != 
        CASE 
            WHEN ps.faction = 'IMPERIAL' THEN m.imperial_team_id
            WHEN ps.faction = 'REBEL' THEN m.rebel_team_id
        END
    LIMIT 10
    """)
    
    mismatches = cursor.fetchall()
    if mismatches:
        print("\nPlayer team_id mismatches (potential subbing):")
        print("-" * 60)
        for m in mismatches:
            print(f"Player: {m['player_name']} ({m['faction']})")
            print(f"  Assigned to: {m['player_team']} (ID: {m['team_id']})")
            print(f"  Match team: {m['match_team']} (ID: {m['expected_team_id']})")
            print(f"  Match ID: {m['match_id']}, Type: {m['match_type']}")
    else:
        print("\nNo team_id mismatches found (players are on the correct teams)")
    
    conn.close()
    print("\nDatabase analysis complete!")
    return True

def main():
    parser = argparse.ArgumentParser(description="Check player and match data to debug ELO ladder issues")
    
    parser.add_argument("--db", type=str, default="squadrons_stats.db",
                       help="SQLite database file path (default: squadrons_stats.db)")
    
    args = parser.parse_args()
    check_match_player_data(args.db)

if __name__ == "__main__":
    main()
