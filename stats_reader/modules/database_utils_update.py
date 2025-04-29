"""
Updated create_database function to include the role column for player_stats
"""

def create_database(db_path):
    """Create the SQLite database with the required schema including role column"""
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
        role TEXT,             -- Added role column (Farmer/Flex/Support)
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
    
    # Check if role column exists in player_stats, and add it if not
    cursor.execute("PRAGMA table_info(player_stats)")
    columns = [col[1] for col in cursor.fetchall()]
    
    if 'role' not in columns:
        print("Adding role column to player_stats table...")
        cursor.execute("ALTER TABLE player_stats ADD COLUMN role TEXT")
        conn.commit()
    
    conn.commit()
    conn.close()
    
    print(f"Database created at {db_path}")
