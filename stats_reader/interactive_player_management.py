"""
Updated interactive_player_management function for reference_manager.py to support roles
"""

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
