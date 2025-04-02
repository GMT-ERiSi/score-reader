"""
Command-line entry point for stats_reader module
"""
import argparse
import sys
from .stats_db_processor import main as stats_processor_main
from .data_cleaner import main as data_cleaner_main

def main():
    parser = argparse.ArgumentParser(description="Star Wars Squadrons Statistics Reader")
    
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Data cleaner command
    cleaner_parser = subparsers.add_parser("clean", help="Clean extracted match data")
    cleaner_parser.add_argument("--input", type=str, required=True,
                      help="Path to the all_seasons_data.json file")
    cleaner_parser.add_argument("--output", type=str,
                      help="Path to save the cleaned data file")
    
    # Stats processor command
    processor_parser = subparsers.add_parser("process", help="Process match data into database and generate stats")
    processor_parser.add_argument("--input", type=str, default="all_seasons_data.json",
                       help="Input JSON file with seasons data (default: all_seasons_data.json)")
    processor_parser.add_argument("--db", type=str, default="squadrons_stats.db",
                       help="SQLite database file path (default: squadrons_stats.db)")
    processor_parser.add_argument("--stats", type=str, default="stats_reports",
                       help="Directory for stats reports (default: stats_reports)")
    processor_parser.add_argument("--generate-only", action="store_true",
                       help="Only generate stats reports from existing database")
    
    args = parser.parse_args()
    
    if args.command is None:
        # For backward compatibility, default to the process command
        print("No command specified, defaulting to 'process'")
        sys.argv.insert(1, "process")
        stats_processor_main()
    elif args.command == "clean":
        # Run the data cleaner
        sys.argv = [sys.argv[0]] + sys.argv[2:]  # Remove the 'clean' argument for the data_cleaner parser
        data_cleaner_main()
    elif args.command == "process":
        # Run the stats processor
        sys.argv = [sys.argv[0]] + sys.argv[2:]  # Remove the 'process' argument for the stats_processor parser
        stats_processor_main()
    else:
        parser.print_help()

if __name__ == "__main__":
    main()