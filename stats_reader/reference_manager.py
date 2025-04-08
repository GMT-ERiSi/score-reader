import os
import sys
import json
import sqlite3
import argparse
import hashlib
import difflib

class ReferenceDatabase:
    """Manages a reference database of canonical player and team information"""
    
    def __init__(self, db_path):
        """Initialize the reference database"""
        self.db_path = db_path
        self.conn = None
        self.initialize_db()
    
    def initialize_db(self):
        """Create the database and tables if they don't exist"""
        self.conn = sqlite3.connect(self.db_path)
        cursor = self.conn.cursor()
        
        # Create teams table - removed faction field
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS ref_teams (
            id INTEGER PRIMARY KEY,
            name TEXT UNIQUE,
            alias TEXT     -- Comma-separated list of alternative names
        )
        ''')
        
        # Create players table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS ref_players (
            id INTEGER PRIMARY KEY,
            name TEXT UNIQUE,
            primary_team_id INTEGER,
            alias TEXT,     -- Comma-separated list of alternative names
            FOREIGN KEY (primary_team_id) REFERENCES ref_teams(id)
        )
        ''')
        
        self.conn.commit()
    
    def close(self):
        """Close the database connection"""
        if self.conn:
            self.conn.close()
    
    def add_team(self, name, alias=None):
        """Add a team to the reference database"""
        try:
            cursor = self.conn.cursor()
            alias_text = ",".join(alias) if alias and isinstance(alias, list) else alias
            cursor.execute(
                "INSERT INTO ref_teams (name, alias) VALUES (?, ?)",
                (name, alias_text)
            )
            self.conn.commit()
            return cursor.lastrowid
        except sqlite3.IntegrityError:
            # Team already exists
            cursor.execute("SELECT id FROM ref_teams WHERE name = ?", (name,))
            result = cursor.fetchone()
            return result[0] if result else None
    
    def add_player(self, name, primary_team_id=None, alias=None):
        """Add a player to the reference database"""
        try:
            cursor = self.conn.cursor()
            alias_text = ",".join(alias) if alias and isinstance(alias, list) else alias
            cursor.execute(
                "INSERT INTO ref_players (name, primary_team_id, alias) VALUES (?, ?, ?)",
                (name, primary_team_id, alias_text)
            )
            self.conn.commit()
            return cursor.lastrowid
        except sqlite3.IntegrityError:
            # Player already exists
            cursor.execute("SELECT id FROM ref_players WHERE name = ?", (name,))
            result = cursor.fetchone()
            return result[0] if result else None
    
    def get_team(self, name, fuzzy_match=False, match_threshold=0.85):
        """Get a team from the reference database"""
        cursor = self.conn.cursor()
        
        # Try exact match first
        cursor.execute("SELECT id, name, alias FROM ref_teams WHERE name = ?", (name,))
        result = cursor.fetchone()
        
        if result:
            return {"id": result[0], "name": result[1], "alias": result[2]}
        
        if not fuzzy_match:
            return None
        
        # Try aliases
        cursor.execute("SELECT id, name, alias FROM ref_teams WHERE alias LIKE ?", (f"%{name}%",))
        result = cursor.fetchone()
        
        if result:
            return {"id": result[0], "name": result[1], "alias": result[2]}
        
        # Try fuzzy matching
        cursor.execute("SELECT id, name, alias FROM ref_teams")
        all_teams = cursor.fetchall()
        best_match = None
        best_score = 0
        
        for team in all_teams:
            score = difflib.SequenceMatcher(None, name.lower(), team[1].lower()).ratio()
            if score > best_score and score >= match_threshold:
                best_score = score
                best_match = team
            
            # Also check aliases
            if team[2]:  # If aliases exist
                for alias in team[2].split(','):
                    alias_score = difflib.SequenceMatcher(None, name.lower(), alias.lower()).ratio()
                    if alias_score > best_score and alias_score >= match_threshold:
                        best_score = alias_score
                        best_match = team
        
        if best_match:
            return {"id": best_match[0], "name": best_match[1], "alias": best_match[2], "match_score": best_score}
        
        return None
    
    def get_player(self, name):
        """Get a player from the reference database by exact match on name or alias."""
        cursor = self.conn.cursor()
        
        # Try exact match first
        cursor.execute("""
            SELECT p.id, p.name, p.primary_team_id, t.name, p.alias 
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
                "alias": result[4]
            }
        
        # Try exact match on alias (comma-separated)
        # This query checks if the name exists within the comma-separated alias string
        cursor.execute("""
            SELECT p.id, p.name, p.primary_team_id, t.name, p.alias
            FROM ref_players p
            LEFT JOIN ref_teams t ON p.primary_team_id = t.id
            WHERE ',' || p.alias || ',' LIKE ?
        """, (f"%,{name},%",)) # Pad with commas for exact match within the list
        result = cursor.fetchone()

        if result:
             return {
                 "id": result[0],
                 "name": result[1],
                 "team_id": result[2],
                 "team_name": result[3],
                 "alias": result[4]
             }

        return None # No exact match found on name or alias
    
    def find_fuzzy_player_matches(self, name, match_threshold=0.85):
        """Find potential player matches using fuzzy matching on name and aliases."""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT p.id, p.name, p.primary_team_id, t.name as team_name, p.alias
            FROM ref_players p
            LEFT JOIN ref_teams t ON p.primary_team_id = t.id
        """)
        all_players = cursor.fetchall()
        
        potential_matches = []
        
        for player_row in all_players:
            player_id, player_name, team_id, team_name, alias_str = player_row
            best_score = 0
            matched_on = None

            # Check primary name
            name_score = difflib.SequenceMatcher(None, name.lower(), player_name.lower()).ratio()
            if name_score >= match_threshold and name_score > best_score:
                best_score = name_score
                matched_on = "name"

            # Check aliases
            if alias_str:
                aliases = alias_str.split(',')
                for alias in aliases:
                    alias_score = difflib.SequenceMatcher(None, name.lower(), alias.strip().lower()).ratio()
                    if alias_score >= match_threshold and alias_score > best_score:
                        best_score = alias_score
                        matched_on = f"alias ({alias.strip()})"

            if best_score > 0: # If any score was above threshold
                 potential_matches.append({
                    "id": player_id,
                    "name": player_name,
                    "team_id": team_id,
                    "team_name": team_name,
                    "alias": alias_str,
                    "match_score": best_score,
                    "matched_on": matched_on
                })

        # Sort by score descending
        potential_matches.sort(key=lambda x: x['match_score'], reverse=True)
        
        return potential_matches

    def add_player_alias(self, player_id, new_alias):
        """Adds a new alias to an existing player."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT alias FROM ref_players WHERE id = ?", (player_id,))
        result = cursor.fetchone()
        
        if result is None:
            print(f"Error: Player with ID {player_id} not found.")
            return False

        current_alias_str = result[0]
        aliases = []
        if current_alias_str:
            aliases = [a.strip() for a in current_alias_str.split(',')]
        
        new_alias_stripped = new_alias.strip()
        if new_alias_stripped and new_alias_stripped not in aliases:
            aliases.append(new_alias_stripped)
            updated_alias_str = ",".join(aliases)
            
            cursor.execute("UPDATE ref_players SET alias = ? WHERE id = ?", (updated_alias_str, player_id))
            self.conn.commit()
            return cursor.rowcount > 0
        elif new_alias_stripped in aliases:
             print(f"Alias '{new_alias_stripped}' already exists for player ID {player_id}.")
             return True # Alias already exists, consider it a success
        else:
            print("Error: New alias cannot be empty.")
            return False
    
    def update_team(self, team_id, name=None, alias=None):
        """Update a team in the reference database"""
        cursor = self.conn.cursor()
        updates = []
        params = []
        
        if name is not None:
            updates.append("name = ?")
            params.append(name)
        
        if alias is not None:
            alias_text = ",".join(alias) if isinstance(alias, list) else alias
            updates.append("alias = ?")
            params.append(alias_text)
        
        if not updates:
            return False
        
        params.append(team_id)
        query = f"UPDATE ref_teams SET {', '.join(updates)} WHERE id = ?"
        cursor.execute(query, params)
        self.conn.commit()
        return cursor.rowcount > 0
    
    def update_player(self, player_id, name=None, primary_team_id=None, alias=None):
        """Update a player in the reference database"""
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
        
        if not updates:
            return False
        
        params.append(player_id)
        query = f"UPDATE ref_players SET {', '.join(updates)} WHERE id = ?"
        cursor.execute(query, params)
        self.conn.commit()
        return cursor.rowcount > 0
    
    def list_teams(self):
        """List all teams in the reference database"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT id, name, alias FROM ref_teams ORDER BY name")
        teams = []
        for row in cursor.fetchall():
            teams.append({
                "id": row[0],
                "name": row[1],
                "alias": row[2].split(',') if row[2] else []
            })
        return teams
    
    def list_players(self, team_id=None):
        """List all players in the reference database"""
        cursor = self.conn.cursor()
        if team_id:
            cursor.execute("""
                SELECT p.id, p.name, p.primary_team_id, t.name, p.alias 
                FROM ref_players p
                LEFT JOIN ref_teams t ON p.primary_team_id = t.id
                WHERE p.primary_team_id = ?
                ORDER BY p.name
            """, (team_id,))
        else:
            cursor.execute("""
                SELECT p.id, p.name, p.primary_team_id, t.name, p.alias 
                FROM ref_players p
                LEFT JOIN ref_teams t ON p.primary_team_id = t.id
                ORDER BY p.name
            """)
        
        players = []
        for row in cursor.fetchall():
            players.append({
                "id": row[0],
                "name": row[1],
                "team_id": row[2],
                "team_name": row[3],
                "alias": row[4].split(',') if row[4] else []
            })
        return players
    
    def import_from_json(self, json_file):
        """Import team and player data from a JSON file"""
        try:
            with open(json_file, 'r') as f:
                data = json.load(f)
            
            # Import teams
            if 'teams' in data:
                for team in data['teams']:
                    self.add_team(
                        name=team.get('name'),
                        alias=team.get('alias')
                    )
            
            # Import players
            if 'players' in data:
                for player in data['players']:
                    # Find team ID if team name is provided
                    team_id = None
                    if 'team_name' in player:
                        team = self.get_team(player['team_name'])
                        if team:
                            team_id = team['id']
                    
                    self.add_player(
                        name=player.get('name'),
                        primary_team_id=player.get('team_id', team_id),
                        alias=player.get('alias')
                    )
            
            return True
        except Exception as e:
            print(f"Error importing from JSON: {e}")
            return False
    
    def export_to_json(self, json_file):
        """Export team and player data to a JSON file"""
        try:
            data = {
                'teams': self.list_teams(),
                'players': self.list_players()
            }
            
            with open(json_file, 'w') as f:
                json.dump(data, f, indent=2)
            
            return True
        except Exception as e:
            print(f"Error exporting to JSON: {e}")
            return False

def interactive_team_management(ref_db):
    """Interactive console interface for team management"""
    while True:
        print("\n==== TEAM MANAGEMENT ====")
        print("1. List all teams")
        print("2. Add a new team")
        print("3. Edit a team")
        print("4. Search for a team")
        print("5. Return to main menu")
        
        choice = input("\nEnter your choice (1-5): ").strip()
        
        if choice == "1":
            # List all teams
            teams = ref_db.list_teams()
            print(f"\nFound {len(teams)} teams:")
            for team in teams:
                aliases = ', '.join(team['alias']) if team['alias'] else 'None'
                print(f"ID: {team['id']}, Name: {team['name']}, Aliases: {aliases}")
        
        elif choice == "2":
            # Add a new team
            name = input("Enter team name: ").strip()
            
            aliases_input = input("Enter aliases (comma-separated, or leave empty): ").strip()
            aliases = [a.strip() for a in aliases_input.split(',')] if aliases_input else None
            
            team_id = ref_db.add_team(name, aliases)
            if team_id:
                print(f"Team added successfully! ID: {team_id}")
            else:
                print("Failed to add team. It may already exist.")
        
        elif choice == "3":
            # Edit a team
            team_id_input = input("Enter team ID to edit: ").strip()
            try:
                team_id = int(team_id_input)
                
                # Get current team data
                cursor = ref_db.conn.cursor()
                cursor.execute("SELECT name, alias FROM ref_teams WHERE id = ?", (team_id,))
                team = cursor.fetchone()
                
                if not team:
                    print(f"No team found with ID {team_id}")
                    continue
                
                current_name, current_alias = team
                current_aliases = current_alias.split(',') if current_alias else []
                
                print(f"\nEditing team: {current_name}")
                print(f"Current aliases: {', '.join(current_aliases) if current_aliases else 'None'}")
                
                name = input(f"Enter new name (or leave empty to keep '{current_name}'): ").strip()
                name = name if name else None
                
                aliases_input = input(f"Enter new aliases (comma-separated, or leave empty to keep current): ").strip()
                aliases = [a.strip() for a in aliases_input.split(',')] if aliases_input else None
                
                if ref_db.update_team(team_id, name, aliases):
                    print("Team updated successfully!")
                else:
                    print("No changes were made.")
            
            except ValueError:
                print("Please enter a valid team ID.")
        
        elif choice == "4":
            # Search for a team
            search_term = input("Enter team name to search: ").strip()
            team = ref_db.get_team(search_term, fuzzy_match=True)
            
            if team:
                match_score = team.get('match_score', 'Exact match')
                aliases = team['alias'].split(',') if team['alias'] else []
                print(f"\nFound team: {team['name']} (ID: {team['id']})")
                print(f"Aliases: {', '.join(aliases) if aliases else 'None'}")
                if isinstance(match_score, float):
                    print(f"Match score: {match_score:.2f}")
            else:
                print("No matching team found.")
        
        elif choice == "5":
            # Return to main menu
            break
        
        else:
            print("Invalid choice, please try again.")

def interactive_player_management(ref_db):
    """Interactive console interface for player management"""
    while True:
        print("\n==== PLAYER MANAGEMENT ====")
        print("1. List all players")
        print("2. List players by team")
        print("3. Add a new player")
        print("4. Edit a player")
        print("5. Search for a player")
        print("6. Return to main menu")
        
        choice = input("\nEnter your choice (1-6): ").strip()
        
        if choice == "1":
            # List all players
            players = ref_db.list_players()
            print(f"\nFound {len(players)} players:")
            for player in players:
                team_name = player['team_name'] or 'No team'
                aliases = ', '.join(player['alias']) if player['alias'] else 'None'
                print(f"ID: {player['id']}, Name: {player['name']}, Team: {team_name}, Aliases: {aliases}")
        
        elif choice == "2":
            # List players by team
            teams = ref_db.list_teams()
            print("\nSelect a team:")
            for i, team in enumerate(teams):
                print(f"{i+1}. {team['name']}")
            
            try:
                team_choice = int(input("\nEnter team number: ").strip())
                if 1 <= team_choice <= len(teams):
                    team_id = teams[team_choice-1]['id']
                    players = ref_db.list_players(team_id)
                    print(f"\nPlayers on team {teams[team_choice-1]['name']}:")
                    if players:
                        for player in players:
                            aliases = ', '.join(player['alias']) if player['alias'] else 'None'
                            print(f"ID: {player['id']}, Name: {player['name']}, Aliases: {aliases}")
                    else:
                        print("No players found for this team.")
                else:
                    print("Invalid team number.")
            except ValueError:
                print("Please enter a valid number.")
        
        elif choice == "3":
            # Add a new player
            name = input("Enter player name: ").strip()
            
            # Select team
            print("\nSelect player's primary team:")
            print("0. No team")
            teams = ref_db.list_teams()
            for i, team in enumerate(teams):
                print(f"{i+1}. {team['name']}")
            
            try:
                team_choice = int(input("\nEnter team number: ").strip())
                if team_choice == 0:
                    team_id = None
                elif 1 <= team_choice <= len(teams):
                    team_id = teams[team_choice-1]['id']
                else:
                    print("Invalid team number. Setting to no team.")
                    team_id = None
            except ValueError:
                print("Invalid input. Setting to no team.")
                team_id = None
            
            aliases_input = input("Enter aliases (comma-separated, or leave empty): ").strip()
            aliases = [a.strip() for a in aliases_input.split(',')] if aliases_input else None
            
            player_id = ref_db.add_player(name, team_id, aliases)
            if player_id:
                print(f"Player added successfully! ID: {player_id}")
            else:
                print("Failed to add player. The name may already exist.")
        
        elif choice == "4":
            # Edit a player
            player_id_input = input("Enter player ID to edit: ").strip()
            try:
                player_id = int(player_id_input)
                
                # Get current player data
                cursor = ref_db.conn.cursor()
                cursor.execute("""
                    SELECT p.name, p.primary_team_id, t.name, p.alias 
                    FROM ref_players p
                    LEFT JOIN ref_teams t ON p.primary_team_id = t.id
                    WHERE p.id = ?
                """, (player_id,))
                player = cursor.fetchone()
                
                if not player:
                    print(f"No player found with ID {player_id}")
                    continue
                
                current_name, current_team_id, current_team_name, current_alias = player
                current_aliases = current_alias.split(',') if current_alias else []
                
                print(f"\nEditing player: {current_name}")
                print(f"Current team: {current_team_name or 'No team'}")
                print(f"Current aliases: {', '.join(current_aliases) if current_aliases else 'None'}")
                
                name = input(f"Enter new name (or leave empty to keep '{current_name}'): ").strip()
                name = name if name else None
                
                # Select new team
                print("\nSelect new primary team:")
                print(f"0. No team {' (current)' if not current_team_id else ''}")
                teams = ref_db.list_teams()
                for i, team in enumerate(teams):
                    is_current = ' (current)' if current_team_id and team['id'] == current_team_id else ''
                    print(f"{i+1}. {team['name']}{is_current}")
                print(f"{len(teams)+1}. Keep current team")
                
                try:
                    team_choice = int(input("\nEnter team number: ").strip())
                    if team_choice == 0:
                        team_id = None
                    elif 1 <= team_choice <= len(teams):
                        team_id = teams[team_choice-1]['id']
                    else:
                        team_id = None  # Keep current
                except ValueError:
                    print("Invalid input. Keeping current team.")
                    team_id = None
                
                aliases_input = input(f"Enter new aliases (comma-separated, or leave empty to keep current): ").strip()
                aliases = [a.strip() for a in aliases_input.split(',')] if aliases_input else None
                
                if ref_db.update_player(player_id, name, team_id, aliases):
                    print("Player updated successfully!")
                else:
                    print("No changes were made.")
            
            except ValueError:
                print("Please enter a valid player ID.")
        
        elif choice == "5":
            # Search for a player
            search_term = input("Enter player name to search: ").strip()
            player = ref_db.get_player(search_term) # Exact match search first
            
            if not player:
                print("\nNo exact match found. Searching for fuzzy matches...")
                fuzzy_matches = ref_db.find_fuzzy_player_matches(search_term)
                if fuzzy_matches:
                    print(f"Found {len(fuzzy_matches)} potential matches:")
                    for match in fuzzy_matches:
                         team_name = match['team_name'] or 'No team'
                         aliases = match['alias'] or 'None'
                         print(f"  ID: {match['id']}, Name: {match['name']}, Team: {team_name}, Aliases: {aliases}, Score: {match['match_score']:.2f} (Matched on: {match['matched_on']})")
                else:
                     print("No fuzzy matches found either.")
                # In interactive mode, we just display results, no action needed here.
                continue # Skip the display logic below if no exact match

            
            if player:
                match_score = player.get('match_score', 'Exact match')
                team_name = player['team_name'] or 'No team'
                aliases = player['alias'].split(',') if player['alias'] else []
                print(f"\nFound player: {player['name']} (ID: {player['id']})")
                print(f"Team: {team_name}")
                print(f"Aliases: {', '.join(aliases) if aliases else 'None'}")
                if isinstance(match_score, float):
                    print(f"Match score: {match_score:.2f}")
            else:
                print("No matching player found.")
        
        elif choice == "6":
            # Return to main menu
            break
        
        else:
            print("Invalid choice, please try again.")

def interactive_menu(ref_db):
    """Interactive console interface for reference database management"""
    while True:
        print("\n==== REFERENCE DATABASE MANAGEMENT ====")
        print("1. Team Management")
        print("2. Player Management")
        print("3. Import from JSON")
        print("4. Export to JSON")
        print("5. Exit")
        
        choice = input("\nEnter your choice (1-5): ").strip()
        
        if choice == "1":
            interactive_team_management(ref_db)
        
        elif choice == "2":
            interactive_player_management(ref_db)
        
        elif choice == "3":
            json_file = input("Enter path to JSON file to import: ").strip()
            if os.path.exists(json_file):
                if ref_db.import_from_json(json_file):
                    print("Data imported successfully!")
                else:
                    print("Failed to import data.")
            else:
                print(f"File not found: {json_file}")
        
        elif choice == "4":
            json_file = input("Enter path to save JSON file: ").strip()
            if ref_db.export_to_json(json_file):
                print(f"Data exported successfully to {json_file}")
            else:
                print("Failed to export data.")
        
        elif choice == "5":
            ref_db.close()
            print("Goodbye!")
            break
        
        else:
            print("Invalid choice, please try again.")

def main():
    parser = argparse.ArgumentParser(description="Manage reference database of teams and players")
    
    parser.add_argument("--db", type=str, default="squadrons_reference.db",
                      help="SQLite reference database file path (default: squadrons_reference.db)")
    parser.add_argument("--import-json", type=str,
                      help="Import teams and players from JSON file")
    parser.add_argument("--export-json", type=str,
                      help="Export teams and players to JSON file")
    
    args = parser.parse_args()
    
    ref_db = ReferenceDatabase(args.db)
    
    if args.import_json:
        if os.path.exists(args.import_json):
            if ref_db.import_from_json(args.import_json):
                print(f"Data imported successfully from {args.import_json}")
            else:
                print(f"Failed to import data from {args.import_json}")
        else:
            print(f"File not found: {args.import_json}")
    
    elif args.export_json:
        if ref_db.export_to_json(args.export_json):
            print(f"Data exported successfully to {args.export_json}")
        else:
            print(f"Failed to export data to {args.export_json}")
    
    else:
        # Run interactive mode
        interactive_menu(ref_db)
    
    ref_db.close()

if __name__ == "__main__":
    main()