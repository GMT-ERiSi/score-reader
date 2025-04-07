#!/usr/bin/env python
"""
Utility script to update match dates in the database.
This helps ensure correct chronological ordering for ELO calculations.
"""

import os
import json
import argparse
import sqlite3
from datetime import datetime

def update_match_dates(db_path):
    """
    Check match dates in the database and allow user to fix them
    """
    if not os.path.exists(db_path):
        print(f"Database not found: {db_path}")
        return False
    
    print(f"Connecting to database: {db_path}")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get all matches
    cursor.execute("""
    SELECT m.id, m.match_date, m.filename, 
           t_imp.name as imperial_team, t_reb.name as rebel_team, 
           m.winner, s.name as season
    FROM matches m
    JOIN teams t_imp ON m.imperial_team_id = t_imp.id
    JOIN teams t_reb ON m.rebel_team_id = t_reb.id
    JOIN seasons s ON m.season_id = s.id
    ORDER BY m.id
    """)
    
    matches = cursor.fetchall()
    
    print(f"\nFound {len(matches)} matches in the database")
    if not matches:
        print("No matches to update")
        return False
    
    # Check each match
    updated = False
    for match in matches:
        match_id, match_date, filename, imperial_team, rebel_team, winner, season = match
        
        print(f"\n\nMatch ID: {match_id}")
        print(f"Filename: {filename}")
        print(f"Season: {season}")
        print(f"Teams: {imperial_team} vs {rebel_team}")
        print(f"Winner: {winner}")
        print(f"Current Date: {match_date}")
        
        change = input("\nUpdate date for this match? (y/n): ").strip().lower()
        if change == 'y':
            new_date = input(f"Enter new date (YYYY-MM-DD HH:MM:SS) or leave empty to skip: ").strip()
            if new_date:
                try:
                    # Validate date format
                    datetime.strptime(new_date, '%Y-%m-%d %H:%M:%S')
                    
                    # Update the date
                    cursor.execute("UPDATE matches SET match_date = ? WHERE id = ?", (new_date, match_id))
                    conn.commit()
                    print(f"Date updated to: {new_date}")
                    updated = True
                except ValueError:
                    print("Invalid date format. Please use YYYY-MM-DD HH:MM:SS")
    
    conn.close()
    
    if updated:
        print("\nMatch dates have been updated successfully!")
    else:
        print("\nNo changes made to match dates.")
    
    return updated

def main():
    parser = argparse.ArgumentParser(description="Update match dates in the database")
    
    parser.add_argument("--db", type=str, default="squadrons_stats.db",
                      help="Path to the database file (default: squadrons_stats.db)")
    
    args = parser.parse_args()
    
    print("Match Date Update Utility")
    print("=======================\n")
    
    update_match_dates(args.db)
    
    print("\nUpdate complete.")
    print("Next step: Generate the ELO ladder with 'python -m stats_reader elo'")

if __name__ == "__main__":
    main()
