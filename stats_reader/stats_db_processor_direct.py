import os
import sys
import json
import sqlite3
import argparse
from datetime import datetime

# Add the modules directory to the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
modules_dir = os.path.join(current_dir, 'modules')
sys.path.insert(0, modules_dir)

# Now import the modules directly
from database_utils import create_database, update_match_types_batch
from match_processor import process_seasons_data
from report_generator import generate_stats_reports

# Import the reference database module
try:
    from reference_manager import ReferenceDatabase
except ImportError:
    print("Warning: Reference database manager not found. Team and player consistency features will be disabled.")
    ReferenceDatabase = None


def main():
    parser = argparse.ArgumentParser(description="Process Star Wars Squadrons match data into a SQLite database")
    
    parser.add_argument("--input", type=str, default="all_seasons_data.json",
                        help="Input JSON file with seasons data (default: all_seasons_data.json)")
    parser.add_argument("--db", type=str, default="squadrons_stats.db",
                        help="SQLite database file path (default: squadrons_stats.db)")
    parser.add_argument("--stats", type=str, default="stats_reports",
                        help="Directory for stats reports (default: stats_reports)")
    parser.add_argument("--reference-db", type=str, default="squadrons_reference.db",
                        help="Reference database for canonical team/player names (default: squadrons_reference.db)")
    parser.add_argument("--generate-only", action="store_true",
                        help="Only generate stats reports from existing database")
    parser.add_argument("--update-match-types", action="store_true",
                        help="Update match types for existing matches in the database")
    parser.add_argument("--force-update-match-types", action="store_true",
                        help="Force update of match types, even if they are already set")
    
    args = parser.parse_args()
    
    if args.update_match_types or args.force_update_match_types:
        # Update match types for existing matches
        if not os.path.exists(args.db):
            print(f"Error: Database file not found: {args.db}")
            sys.exit(1)
        
        update_match_types_batch(args.db, force_update=args.force_update_match_types)
    elif args.generate_only:
        # Only generate stats reports
        if not os.path.exists(args.db):
            print(f"Error: Database file not found: {args.db}")
            sys.exit(1)
        
        generate_stats_reports(args.db, args.stats)
    else:
        # Process data and generate stats
        if not os.path.exists(args.input):
            print(f"Error: Input file not found: {args.input}")
            print("Please run the season_processor.py script first to generate the seasons data.")
            sys.exit(1)
        
        ref_db_path = args.reference_db if os.path.exists(args.reference_db) else None
        if not ref_db_path and args.reference_db != "squadrons_reference.db":
            print(f"Warning: Reference database not found at {args.reference_db}")
            print("Processing will continue without reference database.")
        
        if process_seasons_data(args.db, args.input, ref_db_path):
            generate_stats_reports(args.db, args.stats)

if __name__ == "__main__":
    main()
