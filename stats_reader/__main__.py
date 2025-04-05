"""
Command-line entry point for stats_reader module
"""
import argparse
import sys
from .stats_db_processor import main as stats_processor_main
from .data_cleaner import main as data_cleaner_main
from .elo_ladder import main as elo_ladder_main
from .reference_manager import main as reference_manager_main

def main():
    parser = argparse.ArgumentParser(description="Star Wars Squadrons Statistics Reader")
    
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Reference database management command
    ref_parser = subparsers.add_parser("reference", help="Manage reference database of teams and players")
    ref_parser.add_argument("--db", type=str, default="squadrons_reference.db",
                      help="SQLite reference database file path (default: squadrons_reference.db)")
    ref_parser.add_argument("--import-json", type=str,
                      help="Import teams and players from JSON file")
    ref_parser.add_argument("--export-json", type=str,
                      help="Export teams and players to JSON file")
    
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
    processor_parser.add_argument("--reference-db", type=str, default="squadrons_reference.db",
                       help="Reference database for canonical team/player names (default: squadrons_reference.db)")
    processor_parser.add_argument("--generate-only", action="store_true",
                       help="Only generate stats reports from existing database")
    
    # ELO ladder command
    elo_parser = subparsers.add_parser("elo", help="Generate ELO ladder from match data")
    elo_parser.add_argument("--db", type=str, default="squadrons_stats.db",
                      help="SQLite database file path (default: squadrons_stats.db)")
    elo_parser.add_argument("--output", type=str, default="stats_reports",
                      help="Directory for ELO ladder reports (default: stats_reports)")
    elo_parser.add_argument("--starting-elo", type=int, default=1000,
                      help="Starting ELO rating for new teams (default: 1000)")
    elo_parser.add_argument("--k-factor", type=int, default=32,
                      help="K-factor for ELO calculation (default: 32)")
    
    args = parser.parse_args()
    
    if args.command is None:
        # For backward compatibility, default to the process command
        print("No command specified, defaulting to 'process'")
        sys.argv.insert(1, "process")
        stats_processor_main()
    elif args.command == "reference":
        # Run the reference database manager
        sys.argv = [sys.argv[0]] + sys.argv[2:]  # Remove the 'reference' argument for the reference_manager parser
        reference_manager_main()
    elif args.command == "clean":
        # Run the data cleaner
        sys.argv = [sys.argv[0]] + sys.argv[2:]  # Remove the 'clean' argument for the data_cleaner parser
        data_cleaner_main()
    elif args.command == "process":
        # Run the stats processor
        sys.argv = [sys.argv[0]] + sys.argv[2:]  # Remove the 'process' argument for the stats_processor parser
        stats_processor_main()
    elif args.command == "elo":
        # Run the ELO ladder generator
        sys.argv = [sys.argv[0]] + sys.argv[2:]  # Remove the 'elo' argument for the elo_ladder parser
        elo_ladder_main()
    else:
        parser.print_help()

if __name__ == "__main__":
    main()