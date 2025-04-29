#!/usr/bin/env python3
"""
Script to update match_type for existing matches in the database
This is a one-time script to backfill match_type information
"""

import os
import sys
import sqlite3
import argparse

def update_match_types(db_path):
    """
    Update match types for existing matches in the database
    
    Args:
        db_path (str): Path to the SQLite database
    """
    if not os.path.exists(db_path):
        print(f"Error: Database file not found: {db_path}")
        return False
        
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row  # Enable row factory for named columns
    cursor = conn.cursor()
    
    # First, check if match_type column exists
    cursor.execute("PRAGMA table_info(matches)")
    columns = [col['name'] for col in cursor.fetchall()]
    
    if 'match_type' not in columns:
        print("Adding match_type column to matches table...")
        cursor.execute("ALTER TABLE matches ADD COLUMN match_type TEXT DEFAULT 'team';")
        conn.commit()
    
    # Get all matches without a specified match_type
    cursor.execute("""
    SELECT m.id, m.filename, t_imp.name as imperial_team, t_reb.name as rebel_team
    FROM matches m
    JOIN teams t_imp ON m.imperial_team_id = t_imp.id
    JOIN teams t_reb ON m.rebel_team_id = t_reb.id
    WHERE m.match_type IS NULL OR m.match_type = ''
    ORDER BY m.match_date
    """)
    
    matches = [dict(row) for row in cursor.fetchall()]
    
    if not matches:
        print("All matches already have match_type set. Nothing to update.")
        return True
    
    print(f"Found {len(matches)} matches that need match_type updated.")
    
    # Process each match
    for match in matches:
        print(f"\nMatch ID: {match['id']}")
        print(f"Imperial team: {match['imperial_team']}")
        print(f"Rebel team: {match['rebel_team']}")
        print(f"Filename: {match['filename']}")
        
        print("Match types:")
        print("  team   - Organized matches between established teams")
        print("  pickup - Custom games where players are not representing their established teams")
        print("  ranked - Ranked queue matches where players queue individually")
        match_type = input("Enter match type (team/pickup/ranked) [default: team]: ").strip().lower()
        if match_type not in ["pickup", "ranked"]:
            match_type = "team"  # Default to 'team' if not explicitly specified
        
        # Update the match
        cursor.execute(
            "UPDATE matches SET match_type = ? WHERE id = ?", 
            (match_type, match['id'])
        )
        print(f"Updated match ID {match['id']} to type '{match_type}'")
    
    conn.commit()
    conn.close()
    
    print("\nAll matches updated successfully!")
    return True

def main():
    parser = argparse.ArgumentParser(description="Update match types for existing matches in the database")
    
    parser.add_argument("--db", type=str, default="squadrons_stats.db",
                       help="SQLite database file path (default: squadrons_stats.db)")
    
    args = parser.parse_args()
    update_match_types(args.db)

if __name__ == "__main__":
    main()
