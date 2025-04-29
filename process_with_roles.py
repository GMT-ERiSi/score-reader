"""
Script to process a sample of match data with role support.
"""

import os
import json
import sqlite3
import sys
from datetime import datetime
import hashlib

def get_player_role(ref_db_path, player_name):
    """Get a player's primary role from the reference database"""
    if not os.path.exists(ref_db_path):
        return None
        
    conn = sqlite3.connect(ref_db_path)
    cursor = conn.cursor()
    
    # Try exact match first
    cursor.execute("""
    SELECT name, primary_role 
    FROM ref_players 
    WHERE name = ?
    """, (player_name,))
    
    result = cursor.fetchone()
    
    # If no exact match, try case-insensitive match
    if not result:
        cursor.execute("""
        SELECT name, primary_role 
        FROM ref_players 
        WHERE LOWER(name) = LOWER(?)
        """, (player_name,))
        result = cursor.fetchone()
        if result and result[0] != player_name:
            print(f"Note: Found role using case-insensitive match: DB='{result[0]}' vs Match='{player_name}'")
    
    conn.close()
    
    if result:
        return result[1]  # primary_role
    return None

def process_sample_match(json_path, output_db_path, ref_db_path):
    """Process a sample match with role support"""
    if not os.path.exists(json_path):
        print(f"Error: JSON file not found: {json_path}")
        return False
        
    # Read the JSON file
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    # Get the first match from the data
    if not data:
        print("Error: No data found in JSON file")
        return False
        
    season_name = list(data.keys())[0]
    match_file = list(data[season_name].keys())[0]
    match_data = data[season_name][match_file]
    
    print(f"Processing sample match: {match_file}")
    print(f"Match result: {match_data.get('match_result', 'Unknown')}")
    
    # Create the database if it doesn't exist
    conn = sqlite3.connect(output_db_path)
    cursor = conn.cursor()
    
    # Create necessary tables if they don't exist
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
        match_type TEXT,
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
        player_name TEXT,
        player_hash TEXT,
        team_id INTEGER,
        faction TEXT,
        position TEXT,
        role TEXT,
        score INTEGER,
        kills INTEGER,
        deaths INTEGER,
        assists INTEGER,
        ai_kills INTEGER,
        cap_ship_damage INTEGER,
        is_subbing INTEGER DEFAULT 0,
        FOREIGN KEY (match_id) REFERENCES matches(id),
        FOREIGN KEY (player_id) REFERENCES players(id),
        FOREIGN KEY (team_id) REFERENCES teams(id)
    )
    ''')
    
    # Check if role column exists, add it if not
    cursor.execute("PRAGMA table_info(player_stats)")
    columns = [col[1] for col in cursor.fetchall()]
    if 'role' not in columns:
        print("Adding role column to player_stats table...")
        cursor.execute("ALTER TABLE player_stats ADD COLUMN role TEXT")
        conn.commit()
    
    # Extract match details
    match_result = match_data.get("match_result", "UNKNOWN")
    if "IMPERIAL" in match_result.upper() or "EMPIRE" in match_result.upper():
        winner = "IMPERIAL"
    elif "REBEL" in match_result.upper() or "NEW REPUBLIC" in match_result.upper() or "REPUBLIC" in match_result.upper():
        winner = "REBEL"
    else:
        winner = "UNKNOWN"
    
    # Get or create season
    cursor.execute("SELECT id FROM seasons WHERE name = ?", (season_name,))
    result = cursor.fetchone()
    if result:
        season_id = result[0]
    else:
        cursor.execute("INSERT INTO seasons (name) VALUES (?)", (season_name,))
        season_id = cursor.lastrowid
    
    # Get teams data
    teams_data = match_data.get("teams", {})
    imperial_data = teams_data.get("imperial", teams_data.get("Imperial", teams_data.get("empire", teams_data.get("Empire", {}))))
    rebel_data = teams_data.get("rebel", teams_data.get("Rebel", teams_data.get("new_republic", teams_data.get("New Republic", {}))))
    
    # Get player lists
    if isinstance(imperial_data, dict):
        imperial_players = imperial_data.get("players", [])
    else:
        imperial_players = imperial_data if isinstance(imperial_data, list) else []
        
    if isinstance(rebel_data, dict):
        rebel_players = rebel_data.get("players", [])
    else:
        rebel_players = rebel_data if isinstance(rebel_data, list) else []
    
    # Display players
    print("\nIMPERIAL players:")
    for player in imperial_players:
        if isinstance(player, dict):
            player_name = player.get("player", "Unknown")
        else:
            player_name = str(player)
        
        # Get primary role from reference db
        primary_role = get_player_role(ref_db_path, player_name)
        role_info = f" (Role: {primary_role})" if primary_role else ""
        print(f"  - {player_name}{role_info}")
    
    print("\nREBEL players:")
    for player in rebel_players:
        if isinstance(player, dict):
            player_name = player.get("player", "Unknown")
        else:
            player_name = str(player)
        
        # Get primary role from reference db
        primary_role = get_player_role(ref_db_path, player_name)
        role_info = f" (Role: {primary_role})" if primary_role else ""
        print(f"  - {player_name}{role_info}")
    
    # Get team names
    print("\nTest match processing with roles")
    match_type = input("Match type (team/pickup/ranked): ").strip().lower() or "team"
    
    if match_type == "team":
        imperial_team_name = input("\nIMPERIAL Team Name: ").strip() or "Test Imperial Team"
        rebel_team_name = input("REBEL Team Name: ").strip() or "Test Rebel Team"
    else:
        # Auto-assign team names for pickup/ranked
        if match_type == "pickup":
            imperial_team_name = "Imp_pickup_team"
            rebel_team_name = "NR_pickup_team"
        else:  # ranked
            imperial_team_name = "Imperial_ranked_team"
            rebel_team_name = "NR_ranked_team"
        print(f"\nAuto-assigned team names: {imperial_team_name} vs {rebel_team_name}")
    
    # Create teams
    cursor.execute("SELECT id FROM teams WHERE name = ?", (imperial_team_name,))
    result = cursor.fetchone()
    if result:
        imperial_team_id = result[0]
    else:
        cursor.execute("INSERT INTO teams (name) VALUES (?)", (imperial_team_name,))
        imperial_team_id = cursor.lastrowid
    
    cursor.execute("SELECT id FROM teams WHERE name = ?", (rebel_team_name,))
    result = cursor.fetchone()
    if result:
        rebel_team_id = result[0]
    else:
        cursor.execute("INSERT INTO teams (name) VALUES (?)", (rebel_team_name,))
        rebel_team_id = cursor.lastrowid
    
    # Create match record
    match_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("""
    INSERT INTO matches (season_id, imperial_team_id, rebel_team_id, winner, filename, match_date, match_type)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (season_id, imperial_team_id, rebel_team_id, winner, match_file, match_date, match_type))
    match_id = cursor.lastrowid
    
    # Process imperial players
    for player in imperial_players:
        if isinstance(player, dict):
            player_name = player.get("player", "Unknown")
            position = player.get("position", "")
            score = player.get("score", 0)
            kills = player.get("kills", 0)
            deaths = player.get("deaths", 0)
            assists = player.get("assists", 0)
            ai_kills = player.get("ai_kills", 0)
            cap_ship_damage = player.get("cap_ship_damage", 0)
        else:
            player_name = str(player)
            position = ""
            score = 0
            kills = 0
            deaths = 0
            assists = 0
            ai_kills = 0
            cap_ship_damage = 0
        
        # Generate player hash
        import hashlib
        player_hash = player_name.encode('utf-8')
        player_hash = hashlib.sha256(player_hash).hexdigest()[:16]
        
        # Get or create player
        cursor.execute("SELECT id FROM players WHERE name = ?", (player_name,))
        result = cursor.fetchone()
        if result:
            player_id = result[0]
        else:
            cursor.execute("INSERT INTO players (name, player_hash) VALUES (?, ?)", (player_name, player_hash))
            player_id = cursor.lastrowid
        
        # Get primary role from reference db
        primary_role = get_player_role(ref_db_path, player_name)
        print(f"\nPlayer: {player_name} (Primary role: {primary_role or 'None'})")
        
        # Allow role override
        valid_roles = ["Farmer", "Flex", "Support"]
        role_options_str = ", ".join(valid_roles)
        if primary_role:
            role_prompt = f"Enter role for this match ({role_options_str}) or press Enter to keep primary role: "
        else:
            role_prompt = f"Enter role for this match ({role_options_str}) or press Enter for no role: "
        
        user_role = input(role_prompt).strip()
        
        if user_role:
            # Normalize input (capitalize first letter only)
            user_role = user_role[0].upper() + user_role[1:].lower()
            if user_role in valid_roles:
                player_role = user_role
                print(f"Using role for this match: {player_role}")
            else:
                print(f"Invalid role '{user_role}'. Using primary role.")
                player_role = primary_role
        else:
            player_role = primary_role
        
        # Set team_id based on match type
        team_id_value = None if match_type in ['pickup', 'ranked'] else imperial_team_id
        
        # Insert player stats
        cursor.execute("""
        INSERT INTO player_stats (
            match_id, player_id, player_name, player_hash, team_id, faction, position, role,
            score, kills, deaths, assists, ai_kills, cap_ship_damage, is_subbing
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            match_id, player_id, player_name, player_hash, team_id_value, "IMPERIAL", position, player_role,
            score, kills, deaths, assists, ai_kills, cap_ship_damage, 0
        ))
    
    # Process rebel players (similar to imperial)
    for player in rebel_players:
        if isinstance(player, dict):
            player_name = player.get("player", "Unknown")
            position = player.get("position", "")
            score = player.get("score", 0)
            kills = player.get("kills", 0)
            deaths = player.get("deaths", 0)
            assists = player.get("assists", 0)
            ai_kills = player.get("ai_kills", 0)
            cap_ship_damage = player.get("cap_ship_damage", 0)
        else:
            player_name = str(player)
            position = ""
            score = 0
            kills = 0
            deaths = 0
            assists = 0
            ai_kills = 0
            cap_ship_damage = 0
        
        # Generate player hash
        import hashlib
        player_hash = player_name.encode('utf-8')
        player_hash = hashlib.sha256(player_hash).hexdigest()[:16]
        
        # Get or create player
        cursor.execute("SELECT id FROM players WHERE name = ?", (player_name,))
        result = cursor.fetchone()
        if result:
            player_id = result[0]
        else:
            cursor.execute("INSERT INTO players (name, player_hash) VALUES (?, ?)", (player_name, player_hash))
            player_id = cursor.lastrowid
        
        # Get primary role from reference db
        primary_role = get_player_role(ref_db_path, player_name)
        print(f"\nPlayer: {player_name} (Primary role: {primary_role or 'None'})")
        
        # Allow role override
        valid_roles = ["Farmer", "Flex", "Support"]
        role_options_str = ", ".join(valid_roles)
        if primary_role:
            role_prompt = f"Enter role for this match ({role_options_str}) or press Enter to keep primary role: "
        else:
            role_prompt = f"Enter role for this match ({role_options_str}) or press Enter for no role: "
        
        user_role = input(role_prompt).strip()
        
        if user_role:
            # Normalize input (capitalize first letter only)
            user_role = user_role[0].upper() + user_role[1:].lower()
            if user_role in valid_roles:
                player_role = user_role
                print(f"Using role for this match: {player_role}")
            else:
                print(f"Invalid role '{user_role}'. Using primary role.")
                player_role = primary_role
        else:
            player_role = primary_role
        
        # Set team_id based on match type
        team_id_value = None if match_type in ['pickup', 'ranked'] else rebel_team_id
        
        # Insert player stats
        cursor.execute("""
        INSERT INTO player_stats (
            match_id, player_id, player_name, player_hash, team_id, faction, position, role,
            score, kills, deaths, assists, ai_kills, cap_ship_damage, is_subbing
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            match_id, player_id, player_name, player_hash, team_id_value, "REBEL", position, player_role,
            score, kills, deaths, assists, ai_kills, cap_ship_damage, 0
        ))
    
    # Commit changes and close
    conn.commit()
    
    # Generate report
    cursor.execute("""
    SELECT 
        ps.player_name, 
        ps.faction, 
        ps.role,
        ps.score,
        ps.kills,
        ps.deaths
    FROM player_stats ps
    WHERE ps.match_id = ?
    ORDER BY ps.faction, ps.score DESC
    """, (match_id,))
    
    players = cursor.fetchall()
    
    print("\n=== Match Summary ===")
    print(f"Match ID: {match_id}")
    print(f"Winner: {winner}")
    print(f"Match type: {match_type}")
    print(f"\n{'Player':25} {'Faction':10} {'Role':10} {'Score':6} {'K':3} {'D':3}")
    print("-" * 60)
    
    for p in players:
        role = p[2] if p[2] else "None"
        print(f"{p[0]:<25} {p[1]:<10} {role:<10} {p[3]:<6} {p[4]:<3} {p[5]:<3}")
    
    conn.close()
    
    print("\nMatch processed successfully with role support!")
    return True

if __name__ == "__main__":
    # Default paths
    json_path = "Extracted Results/SCL15/SCL15_results.json"
    output_db_path = "squadrons_stats_test.db"
    ref_db_path = "squadrons_reference.db"
    
    # Override with command line arguments if provided
    if len(sys.argv) > 1:
        json_path = sys.argv[1]
    if len(sys.argv) > 2:
        output_db_path = sys.argv[2]
    if len(sys.argv) > 3:
        ref_db_path = sys.argv[3]
    
    print(f"Processing sample match from: {json_path}")
    print(f"Output database: {output_db_path}")
    print(f"Reference database: {ref_db_path}")
    
    process_sample_match(json_path, output_db_path, ref_db_path)
