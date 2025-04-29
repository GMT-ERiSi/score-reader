"""
Updated functions for reference_manager.py to support player roles (Farmer, Flex, Support)
"""

def add_player(self, name, primary_team_id=None, alias=None, primary_role=None, source_file=None):
    """Add a player to the reference database with role support"""
    try:
        cursor = self.conn.cursor()
        alias_text = ",".join(alias) if alias and isinstance(alias, list) else alias
        
        # Validate role if provided
        valid_roles = [None, "Farmer", "Flex", "Support"]
        if primary_role and primary_role not in valid_roles:
            print(f"Invalid role: {primary_role}. Using None instead.")
            primary_role = None
            
        cursor.execute(
            "INSERT INTO ref_players (name, primary_team_id, alias, primary_role, source_file) VALUES (?, ?, ?, ?, ?)",
            (name, primary_team_id, alias_text, primary_role, source_file)
        )
        self.conn.commit()
        return cursor.lastrowid
    except sqlite3.IntegrityError:
        # Player already exists
        cursor.execute("SELECT id FROM ref_players WHERE name = ?", (name,))
        result = cursor.fetchone()
        return result[0] if result else None

def get_player(self, name):
    """Get a player from the reference database (now with role)"""
    cursor = self.conn.cursor()
    
    # Try exact match first
    cursor.execute("""
        SELECT p.id, p.name, p.primary_team_id, t.name, p.alias, p.primary_role
        FROM ref_players p
        LEFT JOIN ref_teams t ON p.primary_team_id = t.id
        WHERE p.name = ?
    """, (name,))
    result = cursor.fetchone()
    
    if result:
        return {
            "id": result[0], 
            "name": result[1], 
            "team_id": result[2], 
            "team_name": result[3], 
            "alias": result[4],
            "role": result[5]
        }
    
    # Try exact match on alias (comma-separated)
    cursor.execute("""
        SELECT p.id, p.name, p.primary_team_id, t.name, p.alias, p.primary_role
        FROM ref_players p
        LEFT JOIN ref_teams t ON p.primary_team_id = t.id
        WHERE p.alias LIKE ? OR p.alias LIKE ? OR p.alias LIKE ? OR p.alias = ?
    """, (f"%,{name},%", f"{name},%", f"%,{name}", name))
    result = cursor.fetchone()

    if result:
         return {
             "id": result[0],
             "name": result[1],
             "team_id": result[2],
             "team_name": result[3],
             "alias": result[4],
             "role": result[5]
         }

    return None

def find_fuzzy_player_matches(self, name, match_threshold=0.85):
    """Find potential player matches using fuzzy matching, now includes role"""
    cursor = self.conn.cursor()
    cursor.execute("""
        SELECT p.id, p.name, p.primary_team_id, t.name as team_name, p.alias, p.primary_role
        FROM ref_players p
        LEFT JOIN ref_teams t ON p.primary_team_id = t.id
    """)
    all_players = cursor.fetchall()
    
    potential_matches = []
    
    for player_row in all_players:
        player_id, player_name, team_id, team_name, alias_str, primary_role = player_row
        best_score = 0
        matched_on = None

        # Check name
        name_score = difflib.SequenceMatcher(None, name.lower(), player_name.lower()).ratio()
        if name_score >= match_threshold:
            best_score = name_score
            matched_on = "name"

        # Check aliases
        if alias_str:
            aliases = alias_str.split(',')
            for alias in aliases:
                alias_score = difflib.SequenceMatcher(None, name.lower(), alias.strip().lower()).ratio()
                if alias_score > best_score and alias_score >= match_threshold:
                    best_score = alias_score
                    matched_on = f"alias ({alias.strip()})"

        if best_score > 0:
             potential_matches.append({
                "id": player_id,
                "name": player_name,
                "team_id": team_id,
                "team_name": team_name,
                "alias": alias_str,
                "role": primary_role,
                "match_score": best_score,
                "matched_on": matched_on
             })

    # Sort by score descending
    potential_matches.sort(key=lambda x: x['match_score'], reverse=True)
    
    return potential_matches

def update_player(self, player_id, name=None, primary_team_id=None, alias=None, primary_role=None):
    """Update a player in the reference database, now with role support"""
    cursor = self.conn.cursor()
    updates = []
    params = []
    
    if name is not None:
        updates.append("name = ?")
        params.append(name)
    
    if primary_team_id is not None:
        updates.append("primary_team_id = ?")
        params.append(primary_team_id)
    
    if alias is not None:
        alias_text = ",".join(alias) if isinstance(alias, list) else alias
        updates.append("alias = ?")
        params.append(alias_text)
    
    if primary_role is not None:
        # Validate role if provided
        valid_roles = [None, "Farmer", "Flex", "Support"]
        if primary_role not in valid_roles and primary_role != "":
            print(f"Invalid role: {primary_role}. Using None instead.")
            primary_role = None
        updates.append("primary_role = ?")
        params.append(primary_role)
    
    if not updates:
        return False
    
    params.append(player_id)
    query = f"UPDATE ref_players SET {', '.join(updates)} WHERE id = ?"
    cursor.execute(query, params)
    self.conn.commit()
    return cursor.rowcount > 0

def list_players(self, team_id=None):
    """List all players in the reference database"""
    cursor = self.conn.cursor()
    if team_id:
        cursor.execute("""
            SELECT p.id, p.name, p.primary_team_id, t.name, p.alias, p.primary_role 
            FROM ref_players p
            LEFT JOIN ref_teams t ON p.primary_team_id = t.id
            WHERE p.primary_team_id = ?
        """, (team_id,))
    else:
        cursor.execute("""
            SELECT p.id, p.name, p.primary_team_id, t.name, p.alias, p.primary_role 
            FROM ref_players p
            LEFT JOIN ref_teams t ON p.primary_team_id = t.id
        """)
    
    players = []
    for row in cursor.fetchall():
        players.append({
            "id": row[0],
            "name": row[1],
            "team_id": row[2],
            "team_name": row[3],
            "alias": row[4].split(',') if row[4] else [],
            "role": row[5]
        })
    return players
