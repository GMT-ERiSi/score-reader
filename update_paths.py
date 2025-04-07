#!/usr/bin/env python
"""
Utility script to update paths after relocating the project directory.
This will help regenerate the SQL database with proper paths.
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

def find_json_files(base_dir):
    """
    Find all JSON files in the directory structure that might contain match data
    """
    json_files = []
    
    for root, dirs, files in os.walk(base_dir):
        for file in files:
            if file.endswith('.json') and 'results' in file.lower():
                json_files.append(os.path.join(root, file))
    
    return json_files

def check_file_paths(base_dir):
    """
    Check for paths in JSON files that might need updating
    """
    json_files = find_json_files(base_dir)
    
    if not json_files:
        print("No relevant JSON files found.")
        return False
    
    print(f"\nFound {len(json_files)} JSON files to check:")
    for file in json_files:
        print(f" - {file}")
    
    for json_file in json_files:
        try:
            with open(json_file, 'r') as f:
                data = json.load(f)
            
            print(f"\nExamining: {json_file}")
            
            # Check if this file contains match results with filenames
            has_filenames = False
            
            # Look for typical match data structure
            if isinstance(data, dict):
                for season, matches in data.items():
                    if isinstance(matches, dict):
                        for filename, match_data in matches.items():
                            if isinstance(match_data, dict) and 'teams' in match_data:
                                has_filenames = True
                                print(f"  Found filename reference: {filename}")
                                break
                    if has_filenames:
                        break
            
            if has_filenames:
                print("  This file contains filename references. You may need to update paths if filenames include paths.")
            else:
                print("  No filename references found in this file.")
            
        except (json.JSONDecodeError, IOError) as e:
            print(f"\nError examining {json_file}: {e}")
    
    print("\nFile check complete.")
    print("NOTE: If you've moved your Screenshots folder, you may need to:")
    print("1. Regenerate all_seasons_data.json with the new paths")
    print("2. Recreate your database, or")
    print("3. Use database commands to update filenames in the matches table")
    
    return True

def main():
    parser = argparse.ArgumentParser(description="Update paths after relocating the project directory")
    
    parser.add_argument("--db", type=str, default="squadrons_stats.db",
                      help="Path to the database file (default: squadrons_stats.db)")
    parser.add_argument("--check-json", action="store_true",
                      help="Check for JSON files with paths that might need updating")
    parser.add_argument("--base-dir", type=str, default=".",
                      help="Base directory to check for JSON files (default: current directory)")
    
    args = parser.parse_args()
    
    print("Path Update Utility")
    print("===================\n")
    
    if args.check_json:
        check_file_paths(args.base_dir)
    
    update_match_dates(args.db)
    
    print("\nPath update actions completed.")

if __name__ == "__main__":
    main()
