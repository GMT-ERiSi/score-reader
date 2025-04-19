"""
Star Wars Squadrons Stats Reader - Modules package
Contains modular components for database operations, player processing, match processing, and report generation
"""

# Import modules for easier access
from .database_utils import create_database, get_or_create_season, get_or_create_team, update_match_types_batch
from .player_processor import generate_player_hash, get_or_create_player, process_player_stats
from .match_processor import process_match_data, process_seasons_data
from .report_generator import generate_stats_reports
