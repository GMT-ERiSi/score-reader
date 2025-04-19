"""
Database utilities for the Star Wars Squadrons statistics database.
Contains functions for creating and managing the SQLite database.
"""

import os
import sqlite3


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
        match_type TEXT, -- Added to store team/pickup/ranked
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


def update_match_types_batch(db_path, force_update=False):
    """
    Update match types for existing matches in the database using a batch approach
    
    Args:
        db_path (str): Path to the SQLite database
    """
    if not os.path.exists(db_path):
        print(f"Error: Database file not found: {db_path}")
        return False
        
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row  # Enable row factory for named columns
    cursor = conn.cursor()
    
    # First, check if match_type column exists
    cursor.execute("PRAGMA table_info(matches)")
    columns = [col['name'] for col in cursor.fetchall()]
    
    if 'match_type' not in columns:
        print("Adding match_type column to matches table...")
        cursor.execute("ALTER TABLE matches ADD COLUMN match_type TEXT DEFAULT 'team';")
        conn.commit()
    
    # Get all matches count
    if force_update:
        cursor.execute("""
        SELECT COUNT(*) as count
        FROM matches
        """)
    else:
        # Get only matches without a specified match_type
        cursor.execute("""
        SELECT COUNT(*) as count
        FROM matches
        WHERE match_type IS NULL OR match_type = ''
        """)
    
    count = cursor.fetchone()['count']
    
    if count == 0 and not force_update:
        print("All matches already have match_type set. Nothing to update.")
        return True
    
    print(f"Found {count} matches that need match_type updated.")
    
    # Let's try to determine match types in a more efficient way
    decision = input("Do you want to set all existing matches to 'team' type? (y/n): ").strip().lower()
    
    if decision == 'y':
        # Set all NULL match_types to 'team'
        cursor.execute("""
        UPDATE matches
        SET match_type = 'team'
        WHERE match_type IS NULL OR match_type = ''
        """)
        conn.commit()
        print(f"Updated {count} matches to type 'team'")
    else:
        # Allow batch setting by season
        if force_update:
            cursor.execute("""
            SELECT s.id, s.name, COUNT(m.id) as match_count
            FROM seasons s
            JOIN matches m ON s.id = m.season_id
            GROUP BY s.id
            ORDER BY s.name
            """)
        else:
            cursor.execute("""
            SELECT s.id, s.name, COUNT(m.id) as match_count
            FROM seasons s
            JOIN matches m ON s.id = m.season_id
            WHERE m.match_type IS NULL OR m.match_type = ''
            GROUP BY s.id
            ORDER BY s.name
            """)
        
        seasons = [dict(row) for row in cursor.fetchall()]
        
        for season in seasons:
            print(f"\nSeason: {season['name']} ({season['match_count']} matches)")
            decision = input(f"Set all matches in this season to a specific type? (team/pickup/ranked/manual): ").strip().lower()
            
            if decision in ['team', 'pickup', 'ranked']:
                # Set all matches in this season to the chosen type
                cursor.execute("""
                UPDATE matches
                SET match_type = ?
                WHERE season_id = ? AND (match_type IS NULL OR match_type = '')
                """, (decision, season['id']))
                conn.commit()
                print(f"Updated {season['match_count']} matches in {season['name']} to type '{decision}'")
            else:
                # Manual handling for this season
                if force_update:
                    cursor.execute("""
                    SELECT m.id, m.filename, t_imp.name as imperial_team, t_reb.name as rebel_team, m.match_type
                    FROM matches m
                    JOIN teams t_imp ON m.imperial_team_id = t_imp.id
                    JOIN teams t_reb ON m.rebel_team_id = t_reb.id
                    WHERE m.season_id = ?
                    ORDER BY m.match_date
                    """, (season['id'],))
                else:
                    cursor.execute("""
                    SELECT m.id, m.filename, t_imp.name as imperial_team, t_reb.name as rebel_team, m.match_type
                    FROM matches m
                    JOIN teams t_imp ON m.imperial_team_id = t_imp.id
                    JOIN teams t_reb ON m.rebel_team_id = t_reb.id
                    WHERE m.season_id = ? AND (m.match_type IS NULL OR m.match_type = '')
                    ORDER BY m.match_date
                    """, (season['id'],))
                
                season_matches = [dict(row) for row in cursor.fetchall()]
                
                for match in season_matches:
                    print(f"\nMatch ID: {match['id']}")
                    print(f"Imperial team: {match['imperial_team']}")
                    print(f"Rebel team: {match['rebel_team']}")
                    print(f"Filename: {match['filename']}")
                    print(f"Current match type: {match['match_type']}")
                    
                    match_type = input("Enter match type (team/pickup/ranked) [default: team]: ").strip().lower()
                    if match_type not in ["pickup", "ranked"]:
                        match_type = "team"  # Default to 'team' if not explicitly specified
                    
                    # Update the match
                    cursor.execute(
                        "UPDATE matches SET match_type = ? WHERE id = ?", 
                        (match_type, match['id'])
                    )
                    print(f"Updated match ID {match['id']} to type '{match_type}'")
                    conn.commit()  # Commit after each update
    
    conn.close()
    
    print("\nAll matches updated successfully!")
    return True
