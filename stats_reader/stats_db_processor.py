import os
import sys
import json
import sqlite3
import argparse
import hashlib
from datetime import datetime

# Import the reference database module
try:
    from .reference_manager import ReferenceDatabase
except ImportError:
    try:
        from reference_manager import ReferenceDatabase
    except ImportError:
        print("Warning: Reference database manager not found. Team and player consistency features will be disabled.")
        ReferenceDatabase = None

def create_database(db_path):
    """Create the SQLite database with the required schema"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create tables
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS seasons (
        id INTEGER PRIMARY KEY,
        name TEXT UNIQUE
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS teams (
        id INTEGER PRIMARY KEY,
        name TEXT UNIQUE,
        reference_id INTEGER,
        wins INTEGER DEFAULT 0,
        losses INTEGER DEFAULT 0
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS matches (
        id INTEGER PRIMARY KEY,
        season_id INTEGER,
        match_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        imperial_team_id INTEGER,
        rebel_team_id INTEGER,
        winner TEXT,
        filename TEXT,
        FOREIGN KEY (season_id) REFERENCES seasons(id),
        FOREIGN KEY (imperial_team_id) REFERENCES teams(id),
        FOREIGN KEY (rebel_team_id) REFERENCES teams(id)
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS players (
        id INTEGER PRIMARY KEY,
        name TEXT UNIQUE,
        reference_id INTEGER,
        player_hash TEXT UNIQUE
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS player_stats (
        id INTEGER PRIMARY KEY,
        match_id INTEGER,
        player_id INTEGER,
        player_name TEXT,      -- Added for direct reference
        player_hash TEXT,      -- Added for consistent player tracking
        team_id INTEGER,
        faction TEXT,
        position TEXT,
        score INTEGER,
        kills INTEGER,
        deaths INTEGER,
        assists INTEGER,
        ai_kills INTEGER,
        cap_ship_damage INTEGER,
        is_subbing INTEGER DEFAULT 0,  -- 0 = not subbing, 1 = subbing
        FOREIGN KEY (match_id) REFERENCES matches(id),
        FOREIGN KEY (player_id) REFERENCES players(id),
        FOREIGN KEY (team_id) REFERENCES teams(id)
    )
    ''')
    
    conn.commit()
    conn.close()
    
    print(f"Database created at {db_path}")

def generate_player_hash(player_name):
    """Generate a consistent hash for a player name"""
    # Use the exact player name without normalization
    normalized_name = player_name # Keep original name
    # Create hash using SHA-256
    hash_object = hashlib.sha256(normalized_name.encode())
    # Return first 16 characters of hex digest (should be sufficient for uniqueness)
    return hash_object.hexdigest()[:16]

def get_or_create_team(conn, team_name, ref_db=None):
    """
    Get a team ID from the database or create it if it doesn't exist.
    If reference database is provided, try to match team to canonical name.
    """
    cursor = conn.cursor()
    
    # Try to find canonical team if reference DB is available
    ref_id = None
    canonical_name = team_name
    
    if ref_db:
        ref_team = ref_db.get_team(team_name, fuzzy_match=True)
        if ref_team:
            ref_id = ref_team['id']
            canonical_name = ref_team['name']
            # If we found a reference match, check if we've already added this team
            cursor.execute("SELECT id FROM teams WHERE reference_id = ?", (ref_id,))
            result = cursor.fetchone()
            if result:
                return result[0]  # Return existing team ID that matches this reference
    
    # Check if team exists by name
    cursor.execute("SELECT id FROM teams WHERE name = ?", (canonical_name,))
    result = cursor.fetchone()
    
    if result:
        # If we found a reference ID but the existing team doesn't have it, update the record
        if ref_id:
            cursor.execute("UPDATE teams SET reference_id = ? WHERE id = ?", (ref_id, result[0]))
            conn.commit()
        return result[0]
    else:
        # Create new team
        cursor.execute("INSERT INTO teams (name, reference_id) VALUES (?, ?)", 
                      (canonical_name, ref_id))
        conn.commit()
        return cursor.lastrowid

# Cache to store resolutions for player names during a single run
player_resolution_cache = {}

def get_or_create_player(conn, player_name, ref_db=None, cache=None):
    """
    Get a player ID from the database or create it if it doesn't exist.
    Handles exact matching, fuzzy matching prompting, and caching results.
    Returns (player_id, canonical_name, player_hash) or (None, original_name, None) if skipped.
    """
    global player_resolution_cache
    if cache is None: # Use global cache if none provided
        cache = player_resolution_cache

    if player_name in cache:
        print(f"Using cached resolution for '{player_name}': {cache[player_name][1]}")
        return cache[player_name]

    cursor = conn.cursor()
    
    ref_id = None
    canonical_name = player_name
    resolved = False

    if ref_db:
        # 1. Try exact match first (name or alias)
        ref_player = ref_db.get_player(player_name)
        if ref_player:
            print(f"Found exact match for '{player_name}': {ref_player['name']} (ID: {ref_player['id']})")
            ref_id = ref_player['id']
            canonical_name = ref_player['name']
            resolved = True
        else:
            # 2. No exact match, try fuzzy matching and prompt user
            print(f"\nNo exact match found for player: '{player_name}'")
            fuzzy_matches = ref_db.find_fuzzy_player_matches(player_name)
            
            options = {}
            if fuzzy_matches:
                print("Potential matches found:")
                for i, match in enumerate(fuzzy_matches):
                    options[str(i+1)] = match
                    team_info = f" (Team: {match['team_name']})" if match['team_name'] else ""
                    print(f"  {i+1}. {match['name']}{team_info} (Score: {match['match_score']:.2f}, Matched on: {match['matched_on']})")
            else:
                print("No potential fuzzy matches found.")

            while not resolved:
                print("\nPlease choose an action:")
                if fuzzy_matches:
                    print("  [Number] - Select the corresponding match above.")
                    print("  A[Number] - Add '{player_name}' as an alias to the selected match.")
                print("  C - Create a new player entry for '{player_name}'.")
                # print("  U - Use '{player_name}' as Unknown/Temporary (no reference link).") # Option removed for simplicity, use Create New
                print("  S - Skip this player for this match.")
                
                choice = input("Your choice: ").strip().upper()

                if choice.isdigit() and choice in options:
                    selected_match = options[choice]
                    ref_id = selected_match['id']
                    canonical_name = selected_match['name']
                    print(f"Selected existing player: {canonical_name}")
                    resolved = True
                elif choice.startswith('A') and choice[1:].isdigit() and choice[1:] in options:
                    selected_match = options[choice[1:]]
                    if ref_db.add_player_alias(selected_match['id'], player_name):
                         print(f"Added '{player_name}' as alias for {selected_match['name']}.")
                         ref_id = selected_match['id']
                         canonical_name = selected_match['name']
                         resolved = True
                    else:
                         print(f"Failed to add alias. Please try again.")
                elif choice == 'C':
                    # Create new player in reference DB (optional: ask for team)
                    # For now, create without team association in ref_db
                    new_ref_id = ref_db.add_player(player_name, primary_team_id=None, alias=None)
                    if new_ref_id:
                        ref_id = new_ref_id
                        canonical_name = player_name
                        print(f"Created new reference player: {canonical_name} (ID: {ref_id})")
                        resolved = True
                    else:
                         print("Failed to create new player in reference DB. It might already exist.")
                         # Re-try exact match in case it was just created concurrently or failed previously
                         ref_player = ref_db.get_player(player_name)
                         if ref_player:
                             ref_id = ref_player['id']
                             canonical_name = ref_player['name']
                             resolved = True
                         else:
                             print("Still cannot find the player. Please choose another option.")

                # elif choice == 'U':
                #     ref_id = None # No reference link
                #     canonical_name = player_name # Use the name as is
                #     print(f"Using '{player_name}' as temporary name.")
                #     resolved = True
                elif choice == 'S':
                    print(f"Skipping player '{player_name}' for this match.")
                    cache[player_name] = (None, player_name, None)
                    return None, player_name, None # Indicate skipped
                else:
                    print("Invalid choice. Please try again.")

    # 3. Now check/create the player in the main stats DB (players table)
    # If we resolved to a reference player, check by reference_id first
    if ref_id is not None:
        cursor.execute("SELECT id, name, player_hash FROM players WHERE reference_id = ?", (ref_id,))
        result = cursor.fetchone()
        if result:
            player_id, db_name, player_hash = result
            # Ensure hash matches the canonical name (in case canonical name was updated)
            expected_hash = generate_player_hash(canonical_name)
            if player_hash != expected_hash:
                 print(f"Updating hash for player {canonical_name} (ID: {player_id})")
                 cursor.execute("UPDATE players SET player_hash = ? WHERE id = ?", (expected_hash, player_id))
                 conn.commit()
                 player_hash = expected_hash
            # Update name if it differs from canonical, keeping the original ID
            if db_name != canonical_name:
                 print(f"Updating name for player ID {player_id} from '{db_name}' to '{canonical_name}'")
                 cursor.execute("UPDATE players SET name = ? WHERE id = ?", (canonical_name, player_id))
                 conn.commit()

            cache[player_name] = (player_id, canonical_name, player_hash)
            return player_id, canonical_name, player_hash
    
    # If no reference match or not found by ref_id, check by canonical_name hash
    player_hash = generate_player_hash(canonical_name)
    cursor.execute("SELECT id, name FROM players WHERE player_hash = ?", (player_hash,))
    result = cursor.fetchone()

    if result:
        player_id, db_name = result
        # If we resolved a reference ID earlier but this record doesn't have it, update it
        if ref_id is not None:
            cursor.execute("UPDATE players SET reference_id = ? WHERE id = ?", (ref_id, player_id))
            conn.commit()
        # Update name if it differs from canonical
        if db_name != canonical_name:
             print(f"Updating name for player ID {player_id} from '{db_name}' to '{canonical_name}' based on hash match.")
             cursor.execute("UPDATE players SET name = ? WHERE id = ?", (canonical_name, player_id))
             conn.commit()
        
        cache[player_name] = (player_id, canonical_name, player_hash)
        return player_id, canonical_name, player_hash
    else:
        # Player not found by ref_id or hash, create new player in stats DB
        print(f"Creating new player record in stats DB for: {canonical_name} (Ref ID: {ref_id})")
        cursor.execute("INSERT INTO players (name, reference_id, player_hash) VALUES (?, ?, ?)",
                      (canonical_name, ref_id, player_hash))
        conn.commit()
        player_id = cursor.lastrowid
        cache[player_name] = (player_id, canonical_name, player_hash)
        return player_id, canonical_name, player_hash

def get_or_create_season(conn, season_name):
    """Get a season ID from the database or create it if it doesn't exist"""
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM seasons WHERE name = ?", (season_name,))
    result = cursor.fetchone()
    
    if result:
        return result[0]
    else:
        cursor.execute("INSERT INTO seasons (name) VALUES (?)", (season_name,))
        conn.commit()
        return cursor.lastrowid

def process_match_data(conn, season_name, filename, match_data, ref_db=None):
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
    import re
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
    
    # Ask user for team names
    print(f"\nProcessing match: {filename}")
    print(f"Match result: {match_result}")
    print(f"Match date (YYYY-MM-DD HH:MM:SS): {match_date or 'Not detected from filename'}")
    user_date = input("Enter match date or press Enter to accept/use current time: ").strip()
    if user_date:
        match_date = user_date
    
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
    
    # If using reference DB, suggest team names
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
    
    # If using reference DB, suggest team names
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
    
    # Insert match record with date if provided
    if match_date:
        cursor.execute("""
        INSERT INTO matches (season_id, imperial_team_id, rebel_team_id, winner, filename, match_date)
        VALUES (?, ?, ?, ?, ?, ?)
        """, (season_id, imperial_team_id, rebel_team_id, winner, filename, match_date))
    else:
        cursor.execute("""
        INSERT INTO matches (season_id, imperial_team_id, rebel_team_id, winner, filename)
        VALUES (?, ?, ?, ?, ?)
        """, (season_id, imperial_team_id, rebel_team_id, winner, filename))
    
    match_id = cursor.lastrowid
    
    # Process imperial players
    for player_data in imperial_players:
        process_player_stats(conn, match_id, imperial_team_id, "IMPERIAL", player_data, ref_db, player_resolution_cache)
    
    # Process rebel players
    for player_data in rebel_players:
        process_player_stats(conn, match_id, rebel_team_id, "REBEL", player_data, ref_db, player_resolution_cache)
    
    conn.commit()
    print(f"Match data processed successfully. Match ID: {match_id}")

def process_player_stats(conn, match_id, team_id, faction, player_data, ref_db=None, cache=None):
    """Process stats for a single player"""
    cursor = conn.cursor()
    
    # Handle different possible formats of player data
    if isinstance(player_data, dict):
        player_name = player_data.get("player", "Unknown")
        position = player_data.get("position", "")
        score = player_data.get("score", 0)
        kills = player_data.get("kills", 0)
        deaths = player_data.get("deaths", 0)
        assists = player_data.get("assists", 0)
        ai_kills = player_data.get("ai_kills", 0)
        cap_ship_damage = player_data.get("cap_ship_damage", 0)
    else:
        # If player_data is just a string (name)
        player_name = str(player_data)
        position = ""
        score = 0
        kills = 0
        deaths = 0
        assists = 0
        ai_kills = 0
        cap_ship_damage = 0
    
    player_id, canonical_name, player_hash = get_or_create_player(conn, player_name, ref_db, cache)

    # If player was skipped during resolution
    if player_id is None:
        return # Don't record stats for skipped players
    
    # If the canonical name is different from the player name in the data, show what was matched
    if canonical_name != player_name:
        print(f"Matched player '{player_name}' to canonical name '{canonical_name}'")
    
    # Check if player is subbing for this team
    is_subbing = False
    if ref_db:
        # Get player's primary team
        # Use the resolved canonical name for checking primary team
        ref_player = ref_db.get_player(canonical_name) # Should be an exact match now
        if ref_player and ref_player.get('team_id'):
            # If player has a primary team and it's different from current team
            cursor.execute("SELECT name FROM teams WHERE id = ?", (team_id,))
            current_team_name = cursor.fetchone()[0] if cursor.fetchone() else "Unknown Team"
            
            if ref_player['team_id'] != team_id:
                # Ask if player is subbing
                sub_response = input(f"Is {canonical_name} subbing for {current_team_name}? (y/n): ").strip().lower()
                is_subbing = sub_response.startswith('y')
    
    # Insert player stats with name, hash, and subbing status
    cursor.execute("""
    INSERT INTO player_stats (
        match_id, player_id, player_name, player_hash, team_id, faction, position,
        score, kills, deaths, assists, ai_kills, cap_ship_damage, is_subbing
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        match_id, player_id, canonical_name, player_hash, team_id, faction, position,
        score, kills, deaths, assists, ai_kills, cap_ship_damage, 1 if is_subbing else 0
    ))

def process_seasons_data(db_path, seasons_data_path, ref_db_path=None):
    global player_resolution_cache # Access the global cache
    player_resolution_cache = {} # Reset cache for each run
    """Process all seasons data from the JSON file"""
    if not os.path.exists(seasons_data_path):
        print(f"Error: Seasons data file not found: {seasons_data_path}")
        return False
    
    from pathlib import Path # Import Path
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
    
    # Create and connect to the database
    create_database(db_path)
    conn = None # Initialize conn to None
    ref_db = None # Initialize ref_db to None
    try:
        conn = sqlite3.connect(db_path)

        # Initialize reference database if path provided
        if ref_db_path and os.path.exists(ref_db_path) and ReferenceDatabase:
            try:
                ref_db = ReferenceDatabase(ref_db_path)
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
                # Pass the ref_db object and the cache
                process_match_data(conn, season_name, filename, match_data, ref_db)

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

def generate_stats_reports(db_path, output_dir):
    """Generate various statistics reports from the database"""
    if not os.path.exists(db_path):
        print(f"Error: Database file not found: {db_path}")
        return False
    
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row  # Enable row factory for named columns
    cursor = conn.cursor()
    
    # 1. Team Standings Report
    cursor.execute("""
    SELECT name, wins, losses, (wins + losses) as games_played, 
           CAST(wins AS FLOAT) / (wins + losses) AS win_rate
    FROM teams
    WHERE (wins + losses) > 0
    ORDER BY win_rate DESC, wins DESC
    """)
    
    team_standings = [dict(row) for row in cursor.fetchall()]
    
    with open(os.path.join(output_dir, "team_standings.json"), 'w') as f:
        json.dump(team_standings, f, indent=2)
    
    # 2. Player Performance Report - now using player_hash for consistency
    cursor.execute("""
    SELECT ps.player_name as name, ps.player_hash as hash,
           COUNT(DISTINCT ps.match_id) as games_played,
           SUM(CASE WHEN ps.is_subbing = 0 THEN 1 ELSE 0 END) as regular_games,
           SUM(CASE WHEN ps.is_subbing = 1 THEN 1 ELSE 0 END) as sub_games,
           SUM(ps.score) as total_score,
           ROUND(AVG(ps.score), 2) as avg_score,
           SUM(ps.kills) as total_kills,
           SUM(ps.deaths) as total_deaths,
           CASE WHEN SUM(ps.deaths) > 0 
                THEN ROUND(CAST(SUM(ps.kills) AS FLOAT) / SUM(ps.deaths), 2)
                ELSE SUM(ps.kills) END as kd_ratio,
           SUM(ps.assists) as total_assists,
           SUM(ps.ai_kills) as total_ai_kills,
           SUM(ps.cap_ship_damage) as total_cap_ship_damage
    FROM player_stats ps
    GROUP BY ps.player_hash
    ORDER BY avg_score DESC
    """)
    
    player_performance = [dict(row) for row in cursor.fetchall()]
    
    with open(os.path.join(output_dir, "player_performance.json"), 'w') as f:
        json.dump(player_performance, f, indent=2)
    
    # 2b. Player Performance Report (Excluding Subs)
    cursor.execute("""
    SELECT ps.player_name as name, ps.player_hash as hash,
           COUNT(DISTINCT ps.match_id) as games_played,
           SUM(ps.score) as total_score,
           ROUND(AVG(ps.score), 2) as avg_score,
           SUM(ps.kills) as total_kills,
           SUM(ps.deaths) as total_deaths,
           CASE WHEN SUM(ps.deaths) > 0 
                THEN ROUND(CAST(SUM(ps.kills) AS FLOAT) / SUM(ps.deaths), 2)
                ELSE SUM(ps.kills) END as kd_ratio,
           SUM(ps.assists) as total_assists,
           SUM(ps.ai_kills) as total_ai_kills,
           SUM(ps.cap_ship_damage) as total_cap_ship_damage
    FROM player_stats ps
    WHERE ps.is_subbing = 0
    GROUP BY ps.player_hash
    ORDER BY avg_score DESC
    """)
    
    player_performance_no_subs = [dict(row) for row in cursor.fetchall()]
    
    with open(os.path.join(output_dir, "player_performance_no_subs.json"), 'w') as f:
        json.dump(player_performance_no_subs, f, indent=2)
    
    # 3. Faction Win Rates
    cursor.execute("""
    SELECT winner, COUNT(*) as wins,
           ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM matches WHERE winner != 'UNKNOWN'), 2) as win_percentage
    FROM matches
    WHERE winner != 'UNKNOWN'
    GROUP BY winner
    """)
    
    faction_win_rates = [dict(row) for row in cursor.fetchall()]
    
    with open(os.path.join(output_dir, "faction_win_rates.json"), 'w') as f:
        json.dump(faction_win_rates, f, indent=2)
    
    # 4. Season Summary
    cursor.execute("""
    SELECT s.name as season, 
           COUNT(m.id) as matches_played,
           SUM(CASE WHEN m.winner = 'IMPERIAL' THEN 1 ELSE 0 END) as imperial_wins,
           SUM(CASE WHEN m.winner = 'REBEL' THEN 1 ELSE 0 END) as rebel_wins
    FROM seasons s
    LEFT JOIN matches m ON s.id = m.season_id
    GROUP BY s.id
    ORDER BY s.name
    """)
    
    season_summary = [dict(row) for row in cursor.fetchall()]
    
    with open(os.path.join(output_dir, "season_summary.json"), 'w') as f:
        json.dump(season_summary, f, indent=2)
    
    # 5. Player's Team History - updated to include subbing info
    cursor.execute("""
    SELECT ps.player_name, ps.player_hash, 
           t.name as team_name, 
           COUNT(DISTINCT ps.match_id) as games_with_team,
           SUM(CASE WHEN ps.is_subbing = 0 THEN 1 ELSE 0 END) as regular_games,
           SUM(CASE WHEN ps.is_subbing = 1 THEN 1 ELSE 0 END) as sub_games
    FROM player_stats ps
    JOIN teams t ON ps.team_id = t.id
    GROUP BY ps.player_hash, t.id
    ORDER BY ps.player_name, games_with_team DESC
    """)
    
    player_teams = [dict(row) for row in cursor.fetchall()]
    
    with open(os.path.join(output_dir, "player_teams.json"), 'w') as f:
        json.dump(player_teams, f, indent=2)
    
    # 6. Subbing Report - focusing on substitutes
    cursor.execute("""
    SELECT 
        p.name as player_name,
        t.name as team_name,
        COUNT(DISTINCT ps.match_id) as games_subbed,
        ROUND(AVG(ps.score), 2) as avg_score,
        SUM(ps.kills) as total_kills,
        SUM(ps.deaths) as total_deaths,
        CASE WHEN SUM(ps.deaths) > 0 
            THEN ROUND(CAST(SUM(ps.kills) AS FLOAT) / SUM(ps.deaths), 2)
            ELSE SUM(ps.kills) END as kd_ratio,
        SUM(ps.assists) as total_assists,
        SUM(ps.cap_ship_damage) as total_cap_ship_damage
    FROM player_stats ps
    JOIN players p ON ps.player_id = p.id
    JOIN teams t ON ps.team_id = t.id
    WHERE ps.is_subbing = 1
    GROUP BY ps.player_id, ps.team_id
    ORDER BY games_subbed DESC, avg_score DESC
    """)
    
    subbing_report = [dict(row) for row in cursor.fetchall()]
    
    with open(os.path.join(output_dir, "subbing_report.json"), 'w') as f:
        json.dump(subbing_report, f, indent=2)
    
    # Print summary of generated reports
    print(f"\nGenerated reports in {output_dir}:")
    print(f"  - Team Standings: {len(team_standings)} teams")
    print(f"  - Player Performance: {len(player_performance)} players")
    print(f"  - Player Performance (No Subs): {len(player_performance_no_subs)} players")
    print(f"  - Faction Win Rates: {len(faction_win_rates)} factions")
    print(f"  - Season Summary: {len(season_summary)} seasons")
    print(f"  - Player Teams: {len(player_teams)} player-team combinations")
    print(f"  - Subbing Report: {len(subbing_report)} player-team sub combinations")
    
    conn.close()
    return True

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
    
    args = parser.parse_args()
    
    if args.generate_only:
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