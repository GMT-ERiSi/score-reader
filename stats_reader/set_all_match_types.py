#!/usr/bin/env python3
"""
Script to forcefully set all match types at once
"""

import os
import sys
import sqlite3
import argparse

def set_all_match_types(db_path, match_type):
    """
    Force set all match types in the database
    
    Args:
        db_path (str): Path to the SQLite database
        match_type (str): Match type to set for all matches
    """
    if not os.path.exists(db_path):
        print(f"Error: Database file not found: {db_path}")
        return False
        
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # First, check match counts
    cursor.execute("SELECT COUNT(*) FROM matches")
    total_matches = cursor.fetchone()[0]
    
    print(f"Found {total_matches} matches in the database.")
    
    # Use raw SQL with explicit transaction to ensure commit
    conn.execute("BEGIN TRANSACTION")
    conn.execute(f"UPDATE matches SET match_type = ?", (match_type,))
    conn.execute("COMMIT")
    
    # Verify immediately after commit
    cursor.execute(f"SELECT COUNT(*), match_type FROM matches GROUP BY match_type")
    counts = cursor.fetchall()
    print("\nMatch type counts after update:")
    for count, type_value in counts:
        print(f"  {type_value}: {count} matches")
    
    # Show a sample of updated matches
    cursor.execute("""
    SELECT m.id, m.match_date, m.match_type, t_imp.name as imperial_team, t_reb.name as rebel_team
    FROM matches m
    JOIN teams t_imp ON m.imperial_team_id = t_imp.id
    JOIN teams t_reb ON m.rebel_team_id = t_reb.id
    LIMIT 5
    """)
    
    print("\nSample of updated matches:")
    print("-" * 70)
    for row in cursor.fetchall():
        print(f"ID: {row[0]}, Date: {row[1]}, Type: {row[2]}, Teams: {row[3]} vs {row[4]}")
    
    conn.close()
    print("\nUpdate complete!")
    return True

def main():
    parser = argparse.ArgumentParser(description="Force set all match types in the database")
    
    parser.add_argument("--db", type=str, default="squadrons_stats.db",
                       help="SQLite database file path (default: squadrons_stats.db)")
    parser.add_argument("--type", type=str, choices=["team", "pickup", "ranked"], required=True,
                       help="Match type to set for all matches (team/pickup/ranked)")
    
    args = parser.parse_args()
    set_all_match_types(args.db, args.type)

if __name__ == "__main__":
    main()
