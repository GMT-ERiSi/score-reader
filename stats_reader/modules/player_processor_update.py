"""
Updated process_player_stats function to handle player roles
"""

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
        if ref_player and 'role' in ref_player:
            primary_role = ref_player.get('role')
            if primary_role in ["Farmer", "Flex", "Support"]:
                player_role = primary_role
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
