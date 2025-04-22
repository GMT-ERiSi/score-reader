"""
Player processing module for Star Wars Squadrons statistics.
Handles player identification, matching, and stats processing.
"""

import hashlib
import sqlite3

# Cache to store resolutions for player names during a single run
player_resolution_cache = {}


def generate_player_hash(player_name):
    """Generate a consistent hash for a player name"""
    # Use the exact player name without normalization
    normalized_name = player_name # Keep original name
    # Create hash using SHA-256
    hash_object = hashlib.sha256(normalized_name.encode())
    # Return first 16 characters of hex digest (should be sufficient for uniqueness)
    return hash_object.hexdigest()[:16]


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

            # Start of the while loop block - ensuring consistent 4-space indentation
            while not resolved:
                print("\nPlease choose an action:")
                if fuzzy_matches:
                    print("  [Number] - Select the corresponding match above.")
                    print("  A[Number] - Add '{player_name}' as an alias to the selected match.")
                print("  C - Create a new player entry for '{player_name}'.")
                print(f"  AA - Add '{player_name}' as an Alias to an existing player.") # New option
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
                # End of 'elif choice == C' block
                
                elif choice == 'AA':
                    # Add as alias to existing player
                    print("\n--- Existing Players in Reference DB ---")
                    all_players = ref_db.list_players()
                    if not all_players:
                        print("No players found in reference DB to add alias to.")
                        continue # Go back to prompt
                    
                    player_id_map = {} # For quick lookup
                    for p in all_players:
                        team_name = p['team_name'] or 'No team'
                        print(f"ID: {p['id']:<5} Name: {p['name']:<25} Team: {team_name}")
                        player_id_map[p['id']] = p['name']
                    print("---------------------------------------")
                    
                    target_id_input = input(f"Enter the ID of the player to add '{player_name}' as an alias to: ").strip()
                    try:
                        target_id = int(target_id_input)
                        if target_id in player_id_map:
                            if ref_db.add_player_alias(target_id, player_name):
                                print(f"Added '{player_name}' as alias for {player_id_map[target_id]} (ID: {target_id}).")
                                # Fetch the canonical details of the target player
                                target_player_details = ref_db.get_player(player_id_map[target_id]) # Use canonical name to get full details
                                if target_player_details:
                                    ref_id = target_player_details['id']
                                    canonical_name = target_player_details['name']
                                    resolved = True
                                else:
                                    print("Error: Could not retrieve details for target player after adding alias.")
                            else:
                                print(f"Failed to add alias. Please try again.")
                        else:
                            print(f"Invalid target player ID: {target_id}")
                    except ValueError:
                        print("Invalid ID format. Please enter a number.")

                elif choice == 'S':
                    print(f"Skipping player '{player_name}' for this match.")
                    cache[player_name] = (None, player_name, None)
                    return None, player_name, None # Indicate skipped
                else:
                    print("Invalid choice. Please try again.")
            # End of the while loop block

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


def process_player_stats(conn, match_id, team_id, faction, player_data, ref_db=None, cache=None, match_type=None):
    """Process stats for a single player including role handling"""
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
    
    # Determine player's role
    player_role = None
    # Get primary role from reference DB if available
    if ref_db:
        ref_player = ref_db.get_player(canonical_name)
        if ref_player and 'primary_role' in ref_player:
            primary_role_raw = ref_player.get('primary_role') # Get the raw value
            if primary_role_raw: # Check if it's not None or empty string
                primary_role_cleaned = primary_role_raw.strip().capitalize() # Clean and normalize case
                if primary_role_cleaned in ["Farmer", "Flex", "Support"]:
                    player_role = primary_role_cleaned # Assign the cleaned role
                    print(f"Using primary role from reference database: {player_role}")
    
    # Allow overriding the role for this match
    valid_roles = ["Farmer", "Flex", "Support"]
    role_options_str = ", ".join(valid_roles)
    if player_role:
        role_prompt = f"Player '{canonical_name}' primary role is '{player_role}'. Enter new role for this match ({role_options_str}) or press Enter to keep primary role: "
    else:
        role_prompt = f"Player '{canonical_name}' has no primary role. Enter role for this match ({role_options_str}) or press Enter for no role: "
    
    user_role = input(role_prompt).strip()
    
    if user_role:
        # Normalize input (capitalize first letter only)
        user_role = user_role.capitalize()
        if user_role in valid_roles:
            player_role = user_role
            print(f"Using role for this match: {player_role}")
        else:
            print(f"Invalid role '{user_role}'. Valid options are: {role_options_str}")
            print(f"Keeping {'primary role: ' + player_role if player_role else 'no role'}")
    
    # Determine if player is subbing, with interactive confirmation
    suggested_subbing = 0 # Default suggestion is 0 (not subbing)
    prompt_user = False # Only prompt if we have enough info

    # For pickup or ranked matches, set team_id to None
    if match_type in ['pickup', 'ranked']:
        # Quietly set team_id to None for pickup/ranked matches
        team_id_value = None
        print(f"Match type is {match_type}, setting team_id to None for player {canonical_name}")
    else:
        # For team matches, keep the team_id as is
        team_id_value = team_id

        # Determine subbing status for regular team matches
        if ref_db:
            ref_player = ref_db.get_player(canonical_name) # Should be an exact match now
            primary_team_id = ref_player.get('team_id') if ref_player else None
            primary_team_name = ref_player.get('team_name') if ref_player else "Unknown"

            # Get current team name
            cursor.execute("SELECT name FROM teams WHERE id = ?", (team_id,))
            fetch_result = cursor.fetchone()
            current_team_name = fetch_result[0] if fetch_result else "Unknown Team"

            if primary_team_name != "Unknown":
                # We know the player's primary team, compare team NAMES instead of IDs
                if primary_team_name != current_team_name:
                    # Team names don't match, suggest they're subbing
                    suggested_subbing = 1
                else:
                    # Team names match, suggest they're not subbing
                    suggested_subbing = 0
                prompt_user = True # We have enough info to prompt

                prompt_message = (
                    f"Player '{canonical_name}' (Primary Team: {primary_team_name}) is playing for '{current_team_name}'. "
                    f"Team names {'DON''T match' if suggested_subbing == 1 else 'MATCH'}. "
                    f"Suggest player IS subbing: {'Yes' if suggested_subbing == 1 else 'No'}. Confirm? (Y/n): "
                )

    # Determine final is_subbing value
    final_is_subbing = suggested_subbing
    if prompt_user and match_type == 'team': # Only prompt for team matches
        user_response = input(prompt_message).strip().lower()
        if user_response == 'n':
            final_is_subbing = 1 - suggested_subbing # Flip the suggestion
        # If 'y' or empty, keep the suggested value (already assigned to final_is_subbing)

    # Insert player stats with name, hash, role, and subbing status
    cursor.execute("""
    INSERT INTO player_stats (
        match_id, player_id, player_name, player_hash, team_id, faction, position, role,
        score, kills, deaths, assists, ai_kills, cap_ship_damage, is_subbing
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        match_id, player_id, canonical_name, player_hash, team_id_value, faction, position, player_role,
        score, kills, deaths, assists, ai_kills, cap_ship_damage, final_is_subbing
    ))
