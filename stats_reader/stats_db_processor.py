import os
import sys
import json
import sqlite3
import argparse
import hashlib
from datetime import datetime

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
    # Convert to lowercase and remove whitespace for consistency
    normalized_name = player_name.lower().strip()
    # Create hash using SHA-256
    hash_object = hashlib.sha256(normalized_name.encode())
    # Return first 16 characters of hex digest (should be sufficient for uniqueness)
    return hash_object.hexdigest()[:16]

def get_or_create_team(conn, team_name):
    """Get a team ID from the database or create it if it doesn't exist"""
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM teams WHERE name = ?", (team_name,))
    result = cursor.fetchone()
    
    if result:
        return result[0]
    else:
        cursor.execute("INSERT INTO teams (name) VALUES (?)", (team_name,))
        conn.commit()
        return cursor.lastrowid

def get_or_create_player(conn, player_name):
    """Get a player ID from the database or create it if it doesn't exist"""
    cursor = conn.cursor()
    
    # Generate player hash
    player_hash = generate_player_hash(player_name)
    
    cursor.execute("SELECT id FROM players WHERE player_hash = ?", (player_hash,))
    result = cursor.fetchone()
    
    if result:
        return result[0], player_name, player_hash
    else:
        cursor.execute("INSERT INTO players (name, player_hash) VALUES (?, ?)", 
                      (player_name, player_hash))
        conn.commit()
        return cursor.lastrowid, player_name, player_hash

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

def process_match_data(conn, season_name, filename, match_data):
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
    
    imperial_team_name = input("\nIMPERIAL Team Name: ").strip()
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
    
    rebel_team_name = input("\nREBEL Team Name: ").strip()
    if not rebel_team_name:
        rebel_team_name = "Unknown REBEL Team"
    
    # Get or create teams
    imperial_team_id = get_or_create_team(conn, imperial_team_name)
    rebel_team_id = get_or_create_team(conn, rebel_team_name)
    
    # Update win/loss records
    if winner == "IMPERIAL":
        cursor.execute("UPDATE teams SET wins = wins + 1 WHERE id = ?", (imperial_team_id,))
        cursor.execute("UPDATE teams SET losses = losses + 1 WHERE id = ?", (rebel_team_id,))
    elif winner == "REBEL":
        cursor.execute("UPDATE teams SET wins = wins + 1 WHERE id = ?", (rebel_team_id,))
        cursor.execute("UPDATE teams SET losses = losses + 1 WHERE id = ?", (imperial_team_id,))
    
    # Insert match record
    cursor.execute("""
    INSERT INTO matches (season_id, imperial_team_id, rebel_team_id, winner, filename)
    VALUES (?, ?, ?, ?, ?)
    """, (season_id, imperial_team_id, rebel_team_id, winner, filename))
    
    match_id = cursor.lastrowid
    
    # Process imperial players
    for player_data in imperial_players:
        process_player_stats(conn, match_id, imperial_team_id, "IMPERIAL", player_data)
    
    # Process rebel players
    for player_data in rebel_players:
        process_player_stats(conn, match_id, rebel_team_id, "REBEL", player_data)
    
    conn.commit()
    print(f"Match data processed successfully. Match ID: {match_id}")

def process_player_stats(conn, match_id, team_id, faction, player_data):
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
    
    player_id, _, player_hash = get_or_create_player(conn, player_name)
    
    # Insert player stats with name and hash
    cursor.execute("""
    INSERT INTO player_stats (
        match_id, player_id, player_name, player_hash, team_id, faction, position,
        score, kills, deaths, assists, ai_kills, cap_ship_damage
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        match_id, player_id, player_name, player_hash, team_id, faction, position,
        score, kills, deaths, assists, ai_kills, cap_ship_damage
    ))

def process_seasons_data(db_path, seasons_data_path):
    """Process all seasons data from the JSON file"""
    if not os.path.exists(seasons_data_path):
        print(f"Error: Seasons data file not found: {seasons_data_path}")
        return False
    
    try:
        with open(seasons_data_path, 'r') as f:
            seasons_data = json.load(f)
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON in seasons data file: {seasons_data_path}")
        return False
    
    # Create and connect to the database
    create_database(db_path)
    conn = sqlite3.connect(db_path)
    
    # Process each season
    for season_name, season_matches in seasons_data.items():
        print(f"\n{'='*50}")
        print(f"Processing season: {season_name}")
        print(f"{'='*50}")
        
        for filename, match_data in season_matches.items():
            process_match_data(conn, season_name, filename, match_data)
    
    conn.close()
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
    
    # 5. Player's Team History
    cursor.execute("""
    SELECT ps.player_name, ps.player_hash, 
           t.name as team_name, 
           COUNT(DISTINCT ps.match_id) as games_with_team
    FROM player_stats ps
    JOIN teams t ON ps.team_id = t.id
    GROUP BY ps.player_hash, t.id
    ORDER BY ps.player_name, games_with_team DESC
    """)
    
    player_teams = [dict(row) for row in cursor.fetchall()]
    
    with open(os.path.join(output_dir, "player_teams.json"), 'w') as f:
        json.dump(player_teams, f, indent=2)
    
    # Print summary of generated reports
    print(f"\nGenerated reports in {output_dir}:")
    print(f"  - Team Standings: {len(team_standings)} teams")
    print(f"  - Player Performance: {len(player_performance)} players")
    print(f"  - Faction Win Rates: {len(faction_win_rates)} factions")
    print(f"  - Season Summary: {len(season_summary)} seasons")
    print(f"  - Player Teams: {len(player_teams)} player-team combinations")
    
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
        
        if process_seasons_data(args.db, args.input):
            generate_stats_reports(args.db, args.stats)

if __name__ == "__main__":
    main()