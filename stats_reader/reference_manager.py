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
        """Get a player from the reference database (now with role)"""
        cursor = self.conn.cursor()
        
        # Try exact match first
        cursor.execute("""
            SELECT p.id, p.name, p.primary_team_id, t.name, p.alias, p.primary_role
            FROM ref_players p
            LEFT JOIN ref_teams t ON p.primary_team_id = t.id
            WHERE UPPER(TRIM(p.name)) = UPPER(?) -- Apply TRIM only to column, UPPER to both
        """, (name,))
        result = cursor.fetchone()
        
        if result:
            return {
                "id": result[0], 
                "name": result[1], 
                "team_id": result[2], 
                "team_name": result[3], 
                "alias": result[4],
                "primary_role": result[5]
            }
        
        # Try exact match on alias (comma-separated)
        # Note: Applying UPPER to the LIKE patterns might require adjustments depending on SQLite version/config
        # For simplicity, let's focus on the direct name match first. We'll keep the alias check as is for now,
        # but the primary issue seems to be the direct name lookup.
        # If the direct match works, we can revisit refining the alias match if needed.
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
                "primary_role": result[5]
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
                    "primary_role": primary_role,
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
                "primary_role": row[5]
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
                        alias=player.get('alias'),
                        source_file=json_file # Pass the source file path
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

    def resolve_duplicate_ids(self):
        """
        Handles merging duplicate player IDs based on user input.
        1. Prompts user for comma-separated IDs (correct first).
        2. Fetches correct name and incorrect names/source files from DB.
        3. Iterates through source JSON files associated with incorrect IDs.
        4. Replaces occurrences of incorrect names with the correct name in JSONs.
        5. Deletes all incorrect ID entries from the reference database.
        """
        ids_input = input("Enter comma-separated duplicate Player IDs, with the correct ID first (e.g., 1,4,7): ").strip()
        if not ids_input:
            print("No IDs entered.")
            return

        try:
            ids = [int(id_str.strip()) for id_str in ids_input.split(',')]
            if len(ids) < 2:
                raise ValueError("Please provide at least two IDs (correct ID followed by duplicates).")
        except ValueError as e:
            print(f"Invalid input: {e}. Please enter comma-separated numbers.")
            return

        correct_id = ids[0]
        incorrect_ids = ids[1:]

        cursor = self.conn.cursor()

        # --- 1. Get Correct Player Name ---
        cursor.execute("SELECT name FROM ref_players WHERE id = ?", (correct_id,))
        result = cursor.fetchone()
        if not result:
            print(f"Error: Correct Player ID {correct_id} not found in the database.")
            return
        correct_name = result[0]
        print(f"\nCorrect player identified: ID={correct_id}, Name='{correct_name}'")

        # --- 2. Get Incorrect Player Details (ID, Name, Source File) ---
        incorrect_player_details = {} # {incorrect_id: {'name': name, 'source_file': source_file}}
        placeholders = ','.join('?' * len(incorrect_ids))
        cursor.execute(f"SELECT id, name, source_file FROM ref_players WHERE id IN ({placeholders})", incorrect_ids)
        rows = cursor.fetchall()

        found_incorrect_ids = set()
        source_files_to_process = {} # {source_file_path: [list of incorrect IDs in this file]}
        ids_without_source = [] # IDs that are manual or have no source recorded

        for incorrect_id, incorrect_name, source_file in rows:
            found_incorrect_ids.add(incorrect_id)
            incorrect_player_details[incorrect_id] = {'name': incorrect_name, 'source_file': source_file}

            if not source_file:
                print(f"Info: Player ID {incorrect_id} (Name: '{incorrect_name}') has no source file recorded.")
                ids_without_source.append(incorrect_id)
            elif source_file == "manual_entry":
                print(f"Info: Player ID {incorrect_id} (Name: '{incorrect_name}') was added manually.")
                ids_without_source.append(incorrect_id)
            else:
                # Group IDs by source file for processing
                if source_file not in source_files_to_process:
                    source_files_to_process[source_file] = []
                source_files_to_process[source_file].append(incorrect_id)

        # Report any requested incorrect IDs that were not found in the DB
        missing_ids = set(incorrect_ids) - found_incorrect_ids
        if missing_ids:
            print(f"Warning: The following requested incorrect Player IDs were not found in DB: {missing_ids}")

        if not found_incorrect_ids:
            print("None of the specified incorrect IDs were found in the database. No action taken.")
            return

        # --- 3. Process Source JSON Files ---
        all_json_updates_successful = True
        if source_files_to_process:
            print("\nProcessing source JSON files for cleaning:")
            for source_file, ids_in_file in source_files_to_process.items():
                print(f"- Cleaning {source_file}...")
                file_changed = False
                # Get the set of incorrect names relevant to *this* file and these IDs
                names_to_replace = {
                    details['name']
                    for inc_id, details in incorrect_player_details.items()
                    if inc_id in ids_in_file
                }
                if not names_to_replace:
                     print(f"  - No corresponding incorrect names found for IDs {ids_in_file}. Skipping file.")
                     continue

                print(f"  - Replacing names: {names_to_replace} with '{correct_name}'")

                try:
                    # Determine input and output filenames
                    base, ext = os.path.splitext(source_file)
                    cleaned_filename = f"{base}_cleaned{ext}"
                    
                    file_to_read = cleaned_filename if os.path.exists(cleaned_filename) else source_file
                    file_to_write = cleaned_filename # Always write to the cleaned file

                    print(f"  - Reading from: {file_to_read}")
                    if not os.path.exists(file_to_read):
                        # If neither original nor cleaned exists, it's an error
                        raise FileNotFoundError(f"Required input file not found: {file_to_read}")

                    with open(file_to_read, 'r', encoding='utf-8') as f:
                        data = json.load(f)

                    # Iterate through the nested structure to find and replace names
                    replacements_made = 0
                    for season_name, season_matches in data.items():
                        for filename, match_data in season_matches.items():
                            teams_data = match_data.get("teams", {})
                            for team_key, team_info in teams_data.items():
                                players = []
                                if isinstance(team_info, dict):
                                    players = team_info.get("players", [])
                                elif isinstance(team_info, list):
                                    players = team_info

                                for player_entry in players:
                                    if isinstance(player_entry, dict):
                                        current_player_name = player_entry.get("player")
                                        # Check if the current name is one we need to replace
                                        if current_player_name in names_to_replace:
                                            if player_entry["player"] != correct_name: # Avoid unnecessary writes
                                                player_entry["player"] = correct_name
                                                file_changed = True # Mark that a change occurred in this run
                                                replacements_made += 1
                    
                    # Save the potentially modified data to the cleaned file
                    # Always save to _cleaned file if we read from it OR if changes were made reading from original
                    if file_to_read == cleaned_filename or file_changed:
                        if file_changed:
                             print(f"  - Made {replacements_made} replacement(s). Saving to {file_to_write}")
                        else:
                             # This happens if we read from _cleaned but made no *new* changes this run
                             print(f"  - No new replacements made. Re-saving {file_to_write} to ensure consistency.")
                        
                        try:
                            with open(file_to_write, 'w', encoding='utf-8') as f:
                                json.dump(data, f, indent=2)
                            print(f"  - Successfully saved data to {file_to_write}")
                        except Exception as e:
                             print(f"  - Error saving cleaned file {file_to_write}: {e}")
                             all_json_updates_successful = False # Mark as failed if save fails
                    else:
                         # This happens if we read the original file and made no changes
                         print(f"  - No instances of specified incorrect names found in {file_to_read}. No cleaned file generated/updated.")

                except FileNotFoundError:
                    # This error now specifically relates to file_to_read
                    print(f"  - Error: Input file not found: {file_to_read}")
                    all_json_updates_successful = False
                except json.JSONDecodeError:
                    print(f"  - Error: Invalid JSON format in {file_to_read}")
                    all_json_updates_successful = False
                except Exception as e:
                    print(f"  - Error processing JSON file {file_to_read}: {e}")
                    all_json_updates_successful = False
        else:
            print("\nNo source JSON files needed processing for the specified incorrect IDs.")

        # --- 4. Delete Incorrect IDs from Reference DB ---
        ids_to_delete = list(found_incorrect_ids) # Delete all incorrect IDs found in DB

        if not ids_to_delete:
             print("\nNo incorrect IDs found in the database to delete.")
             return # Should have already exited if found_incorrect_ids was empty, but safety check

        print(f"\nAttempting to delete {len(ids_to_delete)} incorrect player entries from reference database...")
        if not all_json_updates_successful:
            proceed = input("Warning: Some JSON cleaning steps failed or were skipped. Still delete incorrect IDs from DB? (y/N): ").strip().lower()
            if proceed != 'y':
                print("Database deletion aborted by user.")
                return

        try:
            placeholders = ','.join('?' * len(ids_to_delete))
            cursor.execute(f"DELETE FROM ref_players WHERE id IN ({placeholders})", ids_to_delete)
            self.conn.commit()
            deleted_count = cursor.rowcount
            print(f"Successfully deleted {deleted_count} incorrect player entries from the database.")
        except Exception as e:
            print(f"Error deleting incorrect player IDs from database: {e}")
            self.conn.rollback() # Rollback if deletion fails

        print("\nDuplicate resolution process finished.")


def interactive_player_management(ref_db):
    """Interactive console interface for player management"""
    valid_roles = [None, "Farmer", "Flex", "Support"]
    
    while True:
        print("\n==== PLAYER MANAGEMENT ====")
        print("1. List all players")
        print("2. List players by team")
        print("3. List players by role")  # New option
        print("4. Add a new player")
        print("5. Edit a player")
        print("6. Search for a player")
        print("7. Resolve Duplicate Player IDs")
        print("8. Return to main menu")
        
        choice = input("\nEnter your choice (1-8): ").strip()
        
        if choice == "1":
            # List all players
            players = ref_db.list_players()
            print(f"\nFound {len(players)} players:")
            for player in players:
                team_name = player['team_name'] or 'No team'
                role = player['role'] or 'No role'
                aliases = ', '.join(player['alias']) if player['alias'] else 'None'
                print(f"ID: {player['id']}, Name: {player['name']}, Team: {team_name}, Role: {role}, Aliases: {aliases}")
        
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
                            role = player['role'] or 'No role'
                            aliases = ', '.join(player['alias']) if player['alias'] else 'None'
                            print(f"ID: {player['id']}, Name: {player['name']}, Role: {role}, Aliases: {aliases}")
                    else:
                        print("No players found for this team.")
                else:
                    print("Invalid team number.")
            except ValueError:
                print("Please enter a valid number.")
        
        elif choice == "3":
            # List players by role
            print("\nSelect a role:")
            roles = ["Farmer", "Flex", "Support", "No role"]
            for i, role in enumerate(roles):
                print(f"{i+1}. {role}")
            
            try:
                role_choice = int(input("\nEnter role number: ").strip())
                if 1 <= role_choice <= len(roles):
                    selected_role = roles[role_choice-1]
                    # Handle "No role" as NULL in database
                    db_role = None if selected_role == "No role" else selected_role
                    
                    # Get all players and filter by role
                    all_players = ref_db.list_players()
                    if db_role is None:
                        players = [p for p in all_players if p['role'] is None]
                    else:
                        players = [p for p in all_players if p['role'] == db_role]
                    
                    print(f"\nPlayers with role '{selected_role}':")
                    if players:
                        for player in players:
                            team_name = player['team_name'] or 'No team'
                            aliases = ', '.join(player['alias']) if player['alias'] else 'None'
                            print(f"ID: {player['id']}, Name: {player['name']}, Team: {team_name}, Aliases: {aliases}")
                    else:
                        print(f"No players found with role '{selected_role}'.")
                else:
                    print("Invalid role number.")
            except ValueError:
                print("Please enter a valid number.")
        
        elif choice == "4":
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
                team_id = None if team_choice == 0 else teams[team_choice-1]['id'] if 1 <= team_choice <= len(teams) else None
                
                if team_choice != 0 and (team_choice < 1 or team_choice > len(teams)):
                    print("Invalid team number. Defaulting to No team.")
                
                # Select role
                print("\nSelect player's primary role:")
                print("0. No role")
                print("1. Farmer")
                print("2. Flex")
                print("3. Support")
                
                role_choice = input("\nEnter role number: ").strip()
                role = None
                if role_choice == "1":
                    role = "Farmer"
                elif role_choice == "2":
                    role = "Flex"
                elif role_choice == "3":
                    role = "Support"
                
                player_id = ref_db.add_player(name, team_id, source_file="manual_entry", primary_role=role)
                if player_id:
                    print(f"Player added successfully! ID: {player_id}")
                else:
                    print("Failed to add player. It may already exist.")
            except ValueError:
                print("Please enter a valid number.")
        
        elif choice == "5":
            # Edit a player
            # --- Display list of players first ---
            print("\n--- Players in Reference Database ---")
            players = ref_db.list_players()
            if not players:
                print("No players found in the reference database.")
                continue # Go back to player menu if no players exist
            for player in players:
                team_name = player['team_name'] or 'No team'
                role = player['role'] or 'No role'
                print(f"ID: {player['id']:<5} Name: {player['name']:<25} Team: {team_name:<20} Role: {role}")
            print("------------------------------------")
            # --- Now ask for the ID ---
            player_id_input = input("Enter player ID to edit: ").strip()
            try:
                player_id = int(player_id_input)
                
                # Get current player data
                cursor = ref_db.conn.cursor()
                cursor.execute("""
                    SELECT p.name, p.primary_team_id, t.name, p.alias, p.primary_role
                    FROM ref_players p
                    LEFT JOIN ref_teams t ON p.primary_team_id = t.id
                    WHERE p.id = ?
                """, (player_id,))
                player = cursor.fetchone()
                
                if not player:
                    print(f"No player found with ID {player_id}")
                    continue
                
                current_name, current_team_id, current_team_name, current_alias, current_role = player
                current_aliases = current_alias.split(',') if current_alias else []
                
                print(f"\nEditing player: {current_name}")
                print(f"Current team: {current_team_name or 'No team'}")
                print(f"Current role: {current_role or 'No role'}")
                print(f"Current aliases: {', '.join(current_aliases) if current_aliases else 'None'}")
                
                name = input(f"Enter new name (or leave empty to keep '{current_name}'): ").strip()
                name = name if name else None
                
                # Select team
                team_input = input(f"Enter new Team ID, Name, or Alias (or '0' for No Team, leave empty to keep current): ").strip()
                team_id_to_update = None # Flag to indicate if we should update
                new_team_selected = False # Flag to track if a valid new selection was made

                if team_input:
                    if team_input == '0':
                        team_id = None
                        new_team_selected = True
                        print("Selected: No Team")
                    else:
                        # Try finding team by ID first
                        found_team = None
                        try:
                            potential_id = int(team_input)
                            cursor = ref_db.conn.cursor()
                            cursor.execute("SELECT id, name FROM ref_teams WHERE id = ?", (potential_id,))
                            result = cursor.fetchone()
                            if result:
                                found_team = {"id": result[0], "name": result[1]}
                        except ValueError:
                            # Input wasn't an integer, try finding by name/alias
                            pass

                        # If not found by ID, try by name/alias (exact match)
                        if not found_team:
                            found_team = ref_db.get_team(team_input, fuzzy_match=False) # Use exact match for name/alias

                        if found_team:
                            team_id = found_team['id']
                            new_team_selected = True
                            print(f"Selected Team: {found_team['name']} (ID: {team_id})")
                        else:
                            print(f"Team '{team_input}' not found. Keeping current team.")
                            team_id = current_team_id # Revert to current if not found
                else:
                    # Input was empty, keep current team
                    team_id = current_team_id
                    print("Keeping current team.")

                # Only set the ID to update if a new selection was explicitly made
                if new_team_selected:
                    team_id_to_update = team_id
                else:
                    team_id_to_update = None # Don't update if input was empty or invalid
                
                # Select role
                print("\nSelect new role:")
                print(f"0. Keep current role ({current_role or 'No role'})")
                print("1. No role")
                print("2. Farmer")
                print("3. Flex")
                print("4. Support")
                
                role_choice = input("\nEnter role number: ").strip()
                role_to_update = None
                
                if role_choice == "1":
                    role_to_update = None
                    print("Selected: No role")
                elif role_choice == "2":
                    role_to_update = "Farmer"
                    print("Selected: Farmer")
                elif role_choice == "3":
                    role_to_update = "Flex"
                    print("Selected: Flex")
                elif role_choice == "4":
                    role_to_update = "Support"
                    print("Selected: Support")
                else:
                    print("Keeping current role.")

                aliases_input = input(f"Enter new aliases (comma-separated, or leave empty to keep current): ").strip()
                aliases = [a.strip() for a in aliases_input.split(',')] if aliases_input else None
                
                if ref_db.update_player(player_id, name, team_id_to_update, aliases, role_to_update):
                    print("Player updated successfully!")
                else:
                    print("No changes were made.")
            
            except ValueError:
                print("Please enter a valid player ID.")
        
        elif choice == "6":
            # Search for a player
            search_term = input("Enter player name to search: ").strip()
            player = interactive_player_search(ref_db, search_term)
            
            if player:
                match_score = player.get('match_score', 'Exact match')
                team_name = player['team_name'] or 'No team'
                role = player['role'] or 'No role'
                aliases = player['alias'].split(',') if player['alias'] else []
                print(f"\nFound player: {player['name']} (ID: {player['id']})")
                print(f"Team: {team_name}")
                print(f"Role: {role}")
                print(f"Aliases: {', '.join(aliases) if aliases else 'None'}")
                if isinstance(match_score, float):
                    print(f"Match score: {match_score:.2f}")
            else:
                print("No matching player found.")
        
        elif choice == "7":
            # Resolve Duplicate Player IDs
            ref_db.resolve_duplicate_ids()
        
        elif choice == "8":
            # Return to main menu
            break
        
        else:
            print("Invalid choice, please try again.")

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
            alias = input("Enter aliases (comma-separated): ").strip()
            alias_list = [a.strip() for a in alias.split(',')] if alias else None
            
            team_id = ref_db.add_team(name, alias_list)
            if team_id:
                print(f"Team added successfully! ID: {team_id}")
            else:
                print("Failed to add team. It may already exist.")
        
        elif choice == "3":
            # Edit a team
            team_id_str = input("Enter team ID to edit: ").strip()
            try:
                team_id = int(team_id_str)
                cursor = ref_db.conn.cursor()
                cursor.execute("SELECT name, alias FROM ref_teams WHERE id = ?", (team_id,))
                team = cursor.fetchone()
                
                if not team:
                    print(f"No team found with ID {team_id}")
                    continue
                
                current_name, current_alias = team
                
                print(f"Editing team: {current_name}")
                name = input(f"Enter new name (or leave empty to keep '{current_name}'): ").strip()
                name = name if name else None
                
                aliases = ', '.join(current_alias.split(',')) if current_alias else 'None'
                alias = input(f"Enter new aliases (comma-separated, or leave empty to keep '{aliases}'): ").strip()
                alias_list = [a.strip() for a in alias.split(',')] if alias else None
                
                if ref_db.update_team(team_id, name, alias_list):
                    print("Team updated successfully!")
                else:
                    print("No changes were made.")
            
            except ValueError:
                print("Please enter a valid team ID.")
        
        elif choice == "4":
            # Search for a team
            name = input("Enter team name to search: ").strip()
            fuzzy = input("Use fuzzy matching? (y/n): ").strip().lower() == 'y'
            
            team = ref_db.get_team(name, fuzzy_match=fuzzy)
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

def interactive_player_search(ref_db, search_term, match_threshold=0.85):
    """Search for a player with both exact and fuzzy matching"""
    # Try exact match first
    player = ref_db.get_player(search_term)
    if player:
        return player
    
    # Try fuzzy match
    potential_matches = ref_db.find_fuzzy_player_matches(search_term, match_threshold)
    
    if not potential_matches:
        return None
    
    if len(potential_matches) == 1:
        return potential_matches[0]
    
    # Multiple potential matches, let user choose
    print("\nMultiple potential matches found:")
    for i, match in enumerate(potential_matches[:10]):  # Limit to 10 matches
        team_name = match['team_name'] or 'No team'
        role = match['role'] or 'No role'
        print(f"{i+1}. {match['name']} (Team: {team_name}, Role: {role}, Score: {match['match_score']:.2f})")
    
    if len(potential_matches) > 10:
        print(f"...and {len(potential_matches) - 10} more matches.")
    
    try:
        choice = int(input("\nSelect a player (or 0 to search again): ").strip())
        if 1 <= choice <= len(potential_matches[:10]):
            return potential_matches[choice-1]
        else:
            return None
    except ValueError:
        return None

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

def populate_players_from_json(ref_db, json_path):
    """Reads a seasons data JSON and adds all unique player names to the reference DB."""
    print(f"Attempting to populate reference DB from: {json_path}")
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            seasons_data = json.load(f)
    except FileNotFoundError:
        print(f"Error: JSON file not found at {json_path}")
        return
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON format in {json_path}")
        return
    except Exception as e:
        print(f"Error reading JSON file {json_path}: {e}")
        return

    unique_players = set()
    player_count = 0
    match_count = 0

    for season_name, season_matches in seasons_data.items():
        for filename, match_data in season_matches.items():
            match_count += 1
            teams_data = match_data.get("teams", {})
            for team_key, team_info in teams_data.items():
                # Handle cases where team_info might be a list directly (older format?)
                players = []
                if isinstance(team_info, dict):
                    players = team_info.get("players", [])
                elif isinstance(team_info, list):
                     players = team_info # Assume list contains player data directly

                for player_entry in players:
                    player_name = None
                    if isinstance(player_entry, dict):
                        player_name = player_entry.get("player")
                    elif isinstance(player_entry, str):
                         player_name = player_entry # Handle case where it's just a name string

                    if player_name:
                        unique_players.add(player_name.strip())
                        player_count += 1

    print(f"Found {len(unique_players)} unique player names across {player_count} entries in {match_count} matches.")

    added_count = 0
    skipped_count = 0
    for player_name in sorted(list(unique_players)):
        # Add player without team or alias initially
        player_id = ref_db.add_player(name=player_name, primary_team_id=None, alias=None, source_file=json_path) # Added source_file
        if player_id:
            # Check if it was newly added (lastrowid > 0) or already existed
            # Note: add_player returns existing ID if IntegrityError occurs
            cursor = ref_db.conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM ref_players WHERE name = ?", (player_name,))
            # This check isn't perfect as add_player returns ID even if exists,
            # but we can infer based on whether it *was* added or *already* existed.
            # A better way might be to check existence before calling add_player.
            # For simplicity, we'll just report based on the set size.
            added_count += 1 # Count all unique names processed
        else:
             # This case shouldn't happen often with current add_player logic unless name is empty
             skipped_count += 1


    print(f"Processed {added_count} unique player names into the reference database.")
    if skipped_count > 0:
        print(f"Skipped {skipped_count} entries (potentially empty or error).")


def main():
    parser = argparse.ArgumentParser(description="Manage the Squadrons reference database.")
    parser.add_argument('--db', default='squadrons_reference.db', help='Path to the reference SQLite database file (default: squadrons_reference.db).')
    parser.add_argument('--manage', action='store_true', help='Enter interactive management mode.')
    parser.add_argument('--import-json', help='Path to a reference JSON file (teams/players structure) to import data from.')
    parser.add_argument('--export-json', help='Path to export the reference database data to JSON.')
    parser.add_argument('--populate-from-json', help='Path to a seasons data JSON file (like all_seasons_data.json) to populate initial player names from.')

    args = parser.parse_args()

    # Ensure the database directory exists if specified with a path
    db_dir = os.path.dirname(args.db)
    if db_dir and not os.path.exists(db_dir):
        os.makedirs(db_dir)
        print(f"Created directory for database: {db_dir}")

    try:
        ref_db = ReferenceDatabase(args.db)

        if args.populate_from_json:
            populate_players_from_json(ref_db, args.populate_from_json)
        elif args.manage:
            interactive_menu(ref_db)
        elif args.import_json:
            if ref_db.import_from_json(args.import_json):
                print(f"Data imported successfully from {args.import_json}")
            else:
                print(f"Failed to import data from {args.import_json}")
        elif args.export_json:
            if ref_db.export_to_json(args.export_json):
                print(f"Data exported successfully from {args.export_json}")
            else:
                print(f"Failed to export data to {args.export_json}")
        else:
             # Default action if no specific mode is chosen could be to print status or help
             print("Reference DB initialized. Use --manage, --import-json, --export-json, or --populate-from-json.")

    finally:
        if ref_db:
            ref_db.close()
            print("Reference database connection closed.")

if __name__ == "__main__":
    main()