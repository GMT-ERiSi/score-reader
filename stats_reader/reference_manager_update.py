"""
This file contains the changes needed for the initialize_db method in ReferenceDatabase class
to add the primary_role field. Replace this method in reference_manager.py
"""

def initialize_db(self):
    """Create the database and tables if they don't exist"""
    self.conn = sqlite3.connect(self.db_path)
    cursor = self.conn.cursor()
    
    # Create teams table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS ref_teams (
        id INTEGER PRIMARY KEY,
        name TEXT UNIQUE,
        alias TEXT     -- Comma-separated list of alternative names
    )
    ''')
    
    # Create players table with primary_role column
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS ref_players (
        id INTEGER PRIMARY KEY,
        name TEXT UNIQUE,
        primary_team_id INTEGER,
        primary_role TEXT, -- Added primary_role column (Farmer/Flex/Support)
        alias TEXT,     -- Comma-separated list of alternative names
        source_file TEXT, -- Path to the JSON file this player was added from
        FOREIGN KEY (primary_team_id) REFERENCES ref_teams(id)
    )
    ''')
    
    # Check if primary_role column exists, and add it if it doesn't
    cursor.execute("PRAGMA table_info(ref_players)")
    columns = [col[1] for col in cursor.fetchall()]
    
    if 'primary_role' not in columns:
        print("Adding primary_role column to ref_players table...")
        cursor.execute("ALTER TABLE ref_players ADD COLUMN primary_role TEXT")
        self.conn.commit()
    
    self.conn.commit()
