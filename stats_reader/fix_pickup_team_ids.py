#!/usr/bin/env python3
"""
Fix team_id values in pickup matches - setting them to NULL
"""

import os
import sys
import sqlite3
import argparse

def fix_pickup_team_ids(db_path):
    """
    Set team_id to NULL for all player_stats in pickup matches
    
    Args:
        db_path (str): Path to the SQLite database
    """
    if not os.path.exists(db_path):
        print(f"Error: Database file not found: {db_path}")
        return False
        
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # First, check how many records need to be updated
    cursor.execute("""
    SELECT COUNT(*) as count
    FROM player_stats ps
    JOIN matches m ON ps.match_id = m.id
    WHERE m.match_type = 'pickup' AND ps.team_id IS NOT NULL
    """)
    
    count = cursor.fetchone()[0]
    print(f"Found {count} player stat entries in pickup matches with team_id set")
    
    if count == 0:
        print("No records need to be updated.")
        return True
    
    # Get a sample of records to be changed
    cursor.execute("""
    SELECT ps.id, ps.player_name, ps.faction, ps.team_id, t.name as team_name, m.id as match_id
    FROM player_stats ps
    JOIN matches m ON ps.match_id = m.id
    JOIN teams t ON ps.team_id = t.id
    WHERE m.match_type = 'pickup' AND ps.team_id IS NOT NULL
    LIMIT 5
    """)
    
    print("\nSample records to be updated:")
    for row in cursor.fetchall():
        print(f"  {row[1]} ({row[2]}) - Currently team: {row[4]} (ID: {row[3]})")
    
    # Get user confirmation
    confirm = input("\nDo you want to set team_id to NULL for all players in pickup matches? (y/n): ")
    if confirm.strip().lower() != 'y':
        print("Operation cancelled.")
        return False
    
    # Perform the update in a transaction
    cursor.execute("BEGIN TRANSACTION")
    cursor.execute("""
    UPDATE player_stats
    SET team_id = NULL
    WHERE match_id IN (
        SELECT id FROM matches WHERE match_type = 'pickup'
    )
    """)
    cursor.execute("COMMIT")
    
    # Verify the update
    cursor.execute("""
    SELECT COUNT(*) as count
    FROM player_stats ps
    JOIN matches m ON ps.match_id = m.id
    WHERE m.match_type = 'pickup' AND ps.team_id IS NOT NULL
    """)
    
    remaining = cursor.fetchone()[0]
    if remaining == 0:
        print("\nSuccess! All player stats in pickup matches now have team_id set to NULL")
    else:
        print(f"\nWarning: {remaining} records still have team_id set")
    
    conn.close()
    return True

def main():
    parser = argparse.ArgumentParser(description="Fix team_id values in pickup matches")
    
    parser.add_argument("--db", type=str, default="squadrons_stats.db",
                       help="SQLite database file path (default: squadrons_stats.db)")
    
    args = parser.parse_args()
    fix_pickup_team_ids(args.db)

if __name__ == "__main__":
    main()
