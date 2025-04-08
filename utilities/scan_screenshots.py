#!/usr/bin/env python
"""
Utility script to scan for screenshots in the new folder structure
and help verify the paths are correct.
"""

import os
import json
import argparse
import sqlite3
from datetime import datetime
import re

def list_screenshot_files(screenshot_dir=None):
    """
    Find all screenshot files in the Screenshots directory
    """
    if not screenshot_dir:
        # Look for Screenshots folder at same level as project
        project_dir = os.path.dirname(os.path.abspath(__file__))
        parent_dir = os.path.dirname(project_dir)
        screenshot_dir = os.path.join(parent_dir, "Screenshots")
    
    if not os.path.exists(screenshot_dir):
        print(f"Screenshots directory not found at: {screenshot_dir}")
        return []
    
    screenshot_files = []
    extensions = [".png", ".jpg", ".jpeg"]
    
    print(f"Searching for screenshots in: {screenshot_dir}")
    
    for root, dirs, files in os.walk(screenshot_dir):
        for file in files:
            if any(file.lower().endswith(ext) for ext in extensions):
                screenshot_files.append(os.path.join(root, file))
    
    return screenshot_files

def check_for_seasons(screenshot_dir=None):
    """Check for season subdirectories in the Screenshots folder"""
    if not screenshot_dir:
        # Look for Screenshots folder at same level as project
        project_dir = os.path.dirname(os.path.abspath(__file__))
        parent_dir = os.path.dirname(project_dir)
        screenshot_dir = os.path.join(parent_dir, "Screenshots")
    
    if not os.path.exists(screenshot_dir):
        print(f"Screenshots directory not found at: {screenshot_dir}")
        return
    
    seasons = []
    for item in os.listdir(screenshot_dir):
        item_path = os.path.join(screenshot_dir, item)
        if os.path.isdir(item_path) and re.match(r'SCL\d+', item):
            seasons.append(item)
    
    if seasons:
        print(f"Found {len(seasons)} season directories:")
        for season in seasons:
            season_path = os.path.join(screenshot_dir, season)
            screenshots = [f for f in os.listdir(season_path) 
                          if os.path.isfile(os.path.join(season_path, f)) and 
                          any(f.lower().endswith(ext) for ext in [".png", ".jpg", ".jpeg"])]
            print(f"  - {season}: {len(screenshots)} screenshots")
    else:
        print("No season directories found (looking for folders like 'SCL14', 'SCL15', etc.)")
        print("You might want to organize your screenshots by season.")

def check_database_match(db_path="squadrons_stats.db"):
    """
    Check if filenames in the database match the available screenshots
    """
    if not os.path.exists(db_path):
        print(f"Database not found: {db_path}")
        return
    
    screenshot_files = list_screenshot_files()
    if not screenshot_files:
        return
    
    # Extract just the filenames without path
    screenshot_basenames = [os.path.basename(f) for f in screenshot_files]
    
    print(f"\nChecking database for matches with {len(screenshot_basenames)} screenshots...")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT id, filename FROM matches")
        matches = cursor.fetchall()
        
        if not matches:
            print("No matches found in database.")
            return
        
        print(f"Found {len(matches)} matches in database.")
        
        # Check for matches
        matched = 0
        unmatched = []
        
        for match_id, filename in matches:
            if filename in screenshot_basenames:
                matched += 1
            else:
                unmatched.append((match_id, filename))
        
        print(f"Database matches found: {matched} out of {len(matches)}")
        
        if unmatched:
            print(f"\nUnmatched database entries ({len(unmatched)}):")
            for match_id, filename in unmatched[:10]:  # Show first 10
                print(f"  ID {match_id}: {filename}")
            
            if len(unmatched) > 10:
                print(f"  ... and {len(unmatched) - 10} more")
        
        # Check for screenshots not in database
        db_filenames = [filename for _, filename in matches]
        unused_screenshots = [f for f in screenshot_basenames if f not in db_filenames]
        
        if unused_screenshots:
            print(f"\nScreenshots not in database ({len(unused_screenshots)}):")
            for filename in unused_screenshots[:10]:  # Show first 10
                print(f"  {filename}")
            
            if len(unused_screenshots) > 10:
                print(f"  ... and {len(unused_screenshots) - 10} more")
    
    except sqlite3.Error as e:
        print(f"Database error: {e}")
    
    finally:
        conn.close()

def main():
    parser = argparse.ArgumentParser(description="Scan for screenshots in the new folder structure")
    
    parser.add_argument("--dir", type=str,
                      help="Path to the Screenshots directory (default: ../Screenshots)")
    parser.add_argument("--db", type=str, default="squadrons_stats.db",
                      help="Path to the database file (default: squadrons_stats.db)")
    
    args = parser.parse_args()
    
    print("Screenshot Scanner Utility")
    print("=========================\n")
    
    # Find project directory and guess parent directory
    project_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(project_dir)
    
    print(f"Project directory: {project_dir}")
    print(f"Parent directory: {parent_dir}")
    
    # Look for the Screenshots directory
    screenshot_dir = args.dir if args.dir else os.path.join(parent_dir, "Screenshots")
    
    if os.path.exists(screenshot_dir):
        print(f"Screenshots directory found at: {screenshot_dir}")
    else:
        print(f"Screenshots directory NOT found at: {screenshot_dir}")
        # Try to find in alternate locations
        alt_locations = [
            os.path.join(project_dir, "Screenshots"),
            os.path.join(parent_dir, "screenshots"),
            os.path.join(parent_dir, "Screenshot")
        ]
        
        for loc in alt_locations:
            if os.path.exists(loc):
                print(f"Found alternative screenshots location: {loc}")
                screenshot_dir = loc
                break
    
    # List screenshots
    screenshots = list_screenshot_files(screenshot_dir)
    
    if screenshots:
        print(f"\nFound {len(screenshots)} screenshot files")
        print("Sample screenshots:")
        for s in screenshots[:5]:
            print(f"  {s}")
        if len(screenshots) > 5:
            print(f"  ... and {len(screenshots)-5} more")
    
    # Check for season directories
    print("\nChecking for season directories...")
    check_for_seasons(screenshot_dir)
    
    # Check database matches
    check_database_match(args.db)
    
    print("\nScan complete.")
    
    if screenshots:
        print("\nNext steps:")
        print("1. If needed, organize screenshots into season folders (SCL14, SCL15, etc.)")
        print("2. Run the score extractor to process these screenshots:")
        print("   python -m score_extractor.season_processor --base-dir ../Screenshots")
        print("3. Update match dates in the database to ensure correct ELO calculations")
        print("4. Generate the ELO ladder: python -m stats_reader elo")
    else:
        print("\nNo screenshots found. Please check the location of your Screenshots folder.")

if __name__ == "__main__":
    main()
