"""
Match processing module for Star Wars Squadrons statistics database.
Handles processing match data from JSON files and inserting into database.
"""

import os
import re
import json
import sqlite3  # Added this import
from pathlib import Path

# Import from local modules - will use relative imports when imported from main file
# When used directly, use these imports
try:
    from .database_utils import get_or_create_season, get_or_create_team, create_database
    from .player_processor import process_player_stats, player_resolution_cache
except ImportError:
    try:
        from database_utils import get_or_create_season, get_or_create_team, create_database
        from player_processor import process_player_stats, player_resolution_cache
    except ImportError:
        print("Error: Unable to import database or player modules.")


def process_match_data(conn, season_name, filename, match_data, ref_db=None, match_type=None):
    """Process a single match and add its data to the database"""
    cursor = conn.cursor()
    
    # Get season ID
    season_id = get_or_create_season(conn, season_name)
    
    # Extract match result and normalize
    match_result = match_data.get("match_result", "UNKNOWN")
    if "IMPERIAL" in match_result.upper() or "EMPIRE" in match_result.upper():
        winner = "IMPERIAL"
    elif "REBEL" in match_result.upper() or "NEW REPUBLIC" in match_result.upper() or "REPUBLIC" in match_result.upper():
        winner = "REBEL"
    else:
        winner = "UNKNOWN"
        
    # Try to extract date from filename
    match_date = None
    
    # First check if match_data already has a date (from season_processor)
    if 'match_date' in match_data:
        match_date = match_data['match_date']
        print(f"Using date from extracted data: {match_date}")
    else:
        # Try pattern like "YYYY.MM.DD" or "YYYY-MM-DD"
        date_pattern = re.search(r'(20\d{2})[.-](\d{2})[.-](\d{2})', filename)
        if date_pattern:
            year, month, day = date_pattern.groups()
            match_date = f"{year}-{month}-{day} 12:00:00"  # Default to noon
        
        # Also try pattern like "MM-DD-YY" or "MM.DD.YY"
        if not match_date:
            date_pattern = re.search(r'(\d{2})[.-](\d{2})[.-](\d{2})', filename)
            if date_pattern:
                month, day, year_short = date_pattern.groups()
                # Assume 20xx for the year
                year = f"20{year_short}"
                match_date = f"{year}-{month}-{day} 12:00:00" # Default to noon
            
            # Also try pattern like "DD.MM.YYYY" common in screenshots
            if not match_date:
                date_pattern = re.search(r'(\d{2})[.-](\d{2})[.-](20\d{2})', filename)
                if date_pattern:
                    day, month, year = date_pattern.groups()
                    match_date = f"{year}-{month}-{day} 12:00:00"  # Default to noon
    
    # Get teams data - handle different possible structures in the JSON
    teams_data = match_data.get("teams", {})
    
    # Debug output to understand data structure
    print(f"\nTeams structure: {list(teams_data.keys())}")
    
    # Handle possible variations in team naming in the JSON
    imperial_data = teams_data.get("imperial", teams_data.get("Imperial", teams_data.get("empire", teams_data.get("Empire", {}))))
    rebel_data = teams_data.get("rebel", teams_data.get("Rebel", teams_data.get("new_republic", teams_data.get("New Republic", {}))))
    
    # Get player lists with fallbacks if structure is different
    if isinstance(imperial_data, dict):
        imperial_players = imperial_data.get("players", [])
    else:
        imperial_players = imperial_data if isinstance(imperial_data, list) else []
        
    if isinstance(rebel_data, dict):
        rebel_players = rebel_data.get("players", [])
    else:
        rebel_players = rebel_data if isinstance(rebel_data, list) else []
    
    # Process basic match info
    print(f"\nProcessing match: {filename}")
    print(f"Match result: {match_result}")
    print(f"Match date (YYYY-MM-DD HH:MM:SS): {match_date or 'Not detected from filename'}")
    user_date = input("Enter match date or press Enter to accept/use current time: ").strip()
    if user_date:
        match_date = user_date
    
    # Ask for match type if not provided
    if match_type is None:
        print("\nMatch types:")
        print("  team   - Organized matches between established teams")
        print("  pickup - Custom games where players are not representing their established teams")
        print("  ranked - Ranked queue matches where players queue individually")
        match_type_input = input("Match type (team/pickup/ranked): ").strip().lower()
        if match_type_input == "pickup":
            match_type = "pickup"
        elif match_type_input == "ranked":
            match_type = "ranked"
        else:
            match_type = "team"  # Default to 'team' if not explicitly specified
    
    # Display imperial players
    print("\nIMPERIAL players:")
    if imperial_players:
        for player in imperial_players:
            if isinstance(player, dict):
                print(f"  - {player.get('player', 'Unknown')}")
            else:
                print(f"  - {player}")
    else:
        print("  No IMPERIAL players found in data")
        # Dump the first level of JSON structure to debug
        print(f"  Debug - Teams data structure: {json.dumps(teams_data, indent=2)[:200]}...")
    
    # Display rebel players
    print("\nREBEL players:")
    if rebel_players:
        for player in rebel_players:
            if isinstance(player, dict):
                print(f"  - {player.get('player', 'Unknown')}")
            else:
                print(f"  - {player}")
    else:
        print("  No REBEL players found in data")
        # Dump the first level of JSON structure to debug
        print(f"  Debug - Teams data structure: {json.dumps(teams_data, indent=2)[:200]}...")
    
    # Get team names based on match type
    if match_type == "team":
        # Only prompt for team names for team matches
        
        # If using reference DB, suggest team names for Imperial
        imperial_team_suggestion = ""
        if ref_db and imperial_players:
            # Try to suggest team based on first player's primary team
            first_player_name = imperial_players[0].get('player', imperial_players[0]) if isinstance(imperial_players[0], dict) else imperial_players[0]
            ref_player = ref_db.get_player(first_player_name) # Exact match only for suggestion
            if ref_player and ref_player.get('team_name'):
                imperial_team_suggestion = f" (Suggested: {ref_player['team_name']})"
        
        imperial_team_name = input(f"\nIMPERIAL Team Name{imperial_team_suggestion}: ").strip()
        if not imperial_team_name and imperial_team_suggestion:
            # Use the suggestion if provided and no input given
            imperial_team_name = imperial_team_suggestion.strip(" (Suggested: ").strip(")")
        
        if not imperial_team_name:
            imperial_team_name = "Unknown IMPERIAL Team"
        
        # If using reference DB, suggest team names for Rebel
        rebel_team_suggestion = ""
        if ref_db and rebel_players:
            # Try to suggest team based on first player's primary team
            first_player_name = rebel_players[0].get('player', rebel_players[0]) if isinstance(rebel_players[0], dict) else rebel_players[0]
            ref_player = ref_db.get_player(first_player_name) # Exact match only for suggestion
            if ref_player and ref_player.get('team_name'):
                rebel_team_suggestion = f" (Suggested: {ref_player['team_name']})"
        
        rebel_team_name = input(f"\nREBEL Team Name{rebel_team_suggestion}: ").strip()
        if not rebel_team_name and rebel_team_suggestion:
            # Use the suggestion if provided and no input given
            rebel_team_name = rebel_team_suggestion.strip(" (Suggested: ").strip(")")
        
        if not rebel_team_name:
            rebel_team_name = "Unknown REBEL Team"
    else:
        # For pickup and ranked matches, use automatic team names
        if match_type == "pickup":
            imperial_team_name = "Imp_pickup_team"
            rebel_team_name = "NR_pickup_team"
            print(f"\nUsing auto-assigned team names for pickup match: {imperial_team_name} vs {rebel_team_name}")
        else:  # ranked
            imperial_team_name = "Imperial_ranked_team"
            rebel_team_name = "NR_ranked_team"
            print(f"\nUsing auto-assigned team names for ranked match: {imperial_team_name} vs {rebel_team_name}")
    
    # Get or create teams
    imperial_team_id = get_or_create_team(conn, imperial_team_name, ref_db)
    rebel_team_id = get_or_create_team(conn, rebel_team_name, ref_db)
    
    # Update win/loss records
    if winner == "IMPERIAL":
        cursor.execute("UPDATE teams SET wins = wins + 1 WHERE id = ?", (imperial_team_id,))
        cursor.execute("UPDATE teams SET losses = losses + 1 WHERE id = ?", (rebel_team_id,))
    elif winner == "REBEL":
        cursor.execute("UPDATE teams SET wins = wins + 1 WHERE id = ?", (rebel_team_id,))
        cursor.execute("UPDATE teams SET losses = losses + 1 WHERE id = ?", (imperial_team_id,))
    
    # Insert match record with date and match_type
    if match_date:
        cursor.execute("""
        INSERT INTO matches (season_id, imperial_team_id, rebel_team_id, winner, filename, match_date, match_type)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (season_id, imperial_team_id, rebel_team_id, winner, filename, match_date, match_type))
    else:
        cursor.execute("""
        INSERT INTO matches (season_id, imperial_team_id, rebel_team_id, winner, filename, match_type)
        VALUES (?, ?, ?, ?, ?, ?)
        """, (season_id, imperial_team_id, rebel_team_id, winner, filename, match_type))
    
    match_id = cursor.lastrowid
    
    # Process imperial players
    for player_data in imperial_players:
        process_player_stats(conn, match_id, imperial_team_id, "IMPERIAL", player_data, ref_db, player_resolution_cache, match_type)
    
    # Process rebel players
    for player_data in rebel_players:
        process_player_stats(conn, match_id, rebel_team_id, "REBEL", player_data, ref_db, player_resolution_cache, match_type)
    
    conn.commit()
    print(f"Match data processed successfully. Match ID: {match_id}")


def process_seasons_data(db_path, seasons_data_path, ref_db_path=None):
    """Process all seasons data from the JSON file"""
    global player_resolution_cache # Access the global cache
    player_resolution_cache = {} # Reset cache for each run
    
    if not os.path.exists(seasons_data_path):
        print(f"Error: Seasons data file not found: {seasons_data_path}")
        return False
    
    try:
        # Use pathlib to read the file, ensuring UTF-8
        seasons_data_text = Path(seasons_data_path).read_text(encoding='utf-8')
        seasons_data = json.loads(seasons_data_text) # Load JSON from string
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON in seasons data file: {seasons_data_path}")
        return False
    except Exception as e: # Catch other potential file errors
        print(f"Error reading seasons data file {seasons_data_path}: {e}")
        return False
    
    # Import the reference database module - handle cases where it's nested or direct import
    ref_db_module = None
    try:
        from ..reference_manager import ReferenceDatabase
        ref_db_module = ReferenceDatabase
    except ImportError:
        try:
            from reference_manager import ReferenceDatabase
            ref_db_module = ReferenceDatabase
        except ImportError:
            print("Warning: Reference database manager not found. Team and player consistency features will be disabled.")
            ref_db_module = None
    
    # Create and connect to the database
    create_database(db_path)
    conn = None # Initialize conn to None
    ref_db = None # Initialize ref_db to None

    try:
        conn = sqlite3.connect(db_path)

        # Initialize reference database if path provided
        if ref_db_path and os.path.exists(ref_db_path) and ref_db_module:
            try:
                ref_db = ref_db_module(ref_db_path)
                print(f"Using reference database from: {ref_db_path}")
            except Exception as e:
                print(f"Error initializing reference database: {e}")
                ref_db = None # Ensure ref_db is None if init fails

        # Process each season
        for season_name, season_matches in seasons_data.items():
            print(f"\n{'='*50}")
            print(f"Processing season: {season_name}")
            print(f"{'='*50}")

            for filename, match_data in season_matches.items():
                # Pass ref_db object (which might be None)
                # Check if there's a match_type in the data
                match_type = match_data.get('match_type', None)
                process_match_data(conn, season_name, filename, match_data, ref_db, match_type)

    except Exception as e:
        print(f"An error occurred during process_seasons_data: {e}")
        # Optionally re-raise the exception if needed
        # raise e
        return False # Indicate failure
    finally:
        # Ensure database connections are closed even if errors occur
        if conn:
            conn.close()
            print("Main database connection closed.")
        if ref_db:
            ref_db.close()
            print("Reference database connection closed.")
    
    print("\nAll seasons data processed successfully")
    return True