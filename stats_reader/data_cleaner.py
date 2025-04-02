import os
import sys
import json
import argparse

def clean_data(input_file, output_file=None):
    """
    Interactive utility to review and clean extracted game data.
    
    Args:
        input_file (str): Path to the all_seasons_data.json file
        output_file (str, optional): Path to save the cleaned data file
    
    Returns:
        bool: True if cleaning was successful
    """
    # Set default output file if not specified
    if not output_file:
        base_name = os.path.splitext(input_file)[0]
        output_file = f"{base_name}_cleaned.json"
    
    # Check if input file exists
    if not os.path.exists(input_file):
        print(f"Error: Input file not found: {input_file}")
        return False
    
    # Load the JSON data
    try:
        with open(input_file, 'r') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON file: {e}")
        return False
    
    # Track modifications
    modified = False
    
    # Process each season
    for season_name, season_matches in data.items():
        print(f"\n{'='*50}")
        print(f"REVIEWING SEASON: {season_name}")
        print(f"{'='*50}")
        
        # Process each match in the season
        for filename, match_data in season_matches.items():
            print(f"\n{'='*50}")
            print(f"REVIEWING MATCH: {filename}")
            print(f"{'='*50}")
            
            # Display match data in a nice format
            pretty_print_match(match_data)
            
            # Ask if user wants to edit this match
            choice = input("\nWould you like to edit this match data? (y/n) ").strip().lower()
            if choice == 'y':
                # Edit match data
                match_data = edit_match_data(match_data)
                season_matches[filename] = match_data
                modified = True
                print("\nMatch data updated.")
            else:
                print("\nSkipping to next match.")
    
    # Save modified data if changes were made
    if modified:
        with open(output_file, 'w') as f:
            json.dump(data, f, indent=2)
        print(f"\nCleaned data saved to: {output_file}")
    else:
        print("\nNo changes were made to the data.")
    
    return True

def pretty_print_match(match_data):
    """Print match data in a readable format"""
    match_result = match_data.get("match_result", "UNKNOWN")
    print(f"\nMatch Result: {match_result}")
    
    # Print teams data
    teams_data = match_data.get("teams", {})
    
    # Handle possible variations in team naming
    imperial_data = teams_data.get("imperial", teams_data.get("Imperial", teams_data.get("empire", teams_data.get("Empire", {}))))
    rebel_data = teams_data.get("rebel", teams_data.get("Rebel", teams_data.get("new_republic", teams_data.get("New Republic", {}))))
    
    # Print imperial players
    print("\nIMPERIAL TEAM:")
    print_player_table(imperial_data)
    
    # Print rebel players
    print("\nREBEL TEAM:")
    print_player_table(rebel_data)

def print_player_table(team_data):
    """Print players in a tabular format"""
    # Get player list with fallbacks for different structures
    if isinstance(team_data, dict):
        players = team_data.get("players", [])
    else:
        players = team_data if isinstance(team_data, list) else []
    
    if not players:
        print("  No players found")
        return
    
    # Get a sample player to determine available fields
    sample_player = players[0] if players else {}
    if not isinstance(sample_player, dict):
        # Handle simple player names (not dictionaries)
        for player in players:
            print(f"  - {player}")
        return
    
    # Print header
    headers = ["Player", "Position", "Score", "Kills", "Deaths", "Assists", "AI Kills", "Cap Ship DMG"]
    header_format = "{:<20} {:<15} {:<8} {:<8} {:<8} {:<8} {:<8} {:<10}"
    print(header_format.format(*headers))
    print("-" * 90)
    
    # Print each player
    for player in players:
        if isinstance(player, dict):
            row = [
                player.get("player", "Unknown")[:20],
                player.get("position", "")[:15],
                player.get("score", 0),
                player.get("kills", 0),
                player.get("deaths", 0),
                player.get("assists", 0),
                player.get("ai_kills", 0),
                player.get("cap_ship_damage", 0)
            ]
            try:
                print(header_format.format(*row))
            except Exception as e:
                print(f"Error formatting player: {player}")
                print(f"Error details: {e}")
        else:
            print(f"  - {player}")

def edit_match_data(match_data):
    """Allow user to edit match data interactively"""
    # Create a copy to work with
    edited_data = match_data.copy()
    
    # Main editing menu
    while True:
        print("\nEDIT OPTIONS:")
        print("1. Edit match result")
        print("2. Edit imperial team players")
        print("3. Edit rebel team players")
        print("4. View current match data")
        print("5. Save and exit")
        
        choice = input("\nEnter your choice (1-5): ").strip()
        
        if choice == "1":
            # Edit match result
            current_result = edited_data.get("match_result", "UNKNOWN")
            print(f"\nCurrent match result: {current_result}")
            new_result = input("Enter new match result: ").strip()
            if new_result:
                edited_data["match_result"] = new_result
        
        elif choice == "2" or choice == "3":
            # Edit team players
            team_key = "imperial" if choice == "2" else "rebel"
            
            # Handle possible variations in team naming
            teams_data = edited_data.get("teams", {})
            if choice == "2":
                # Find imperial team key
                for possible_key in ["imperial", "Imperial", "empire", "Empire"]:
                    if possible_key in teams_data:
                        team_key = possible_key
                        break
            else:
                # Find rebel team key
                for possible_key in ["rebel", "Rebel", "new_republic", "New Republic"]:
                    if possible_key in teams_data:
                        team_key = possible_key
                        break
            
            # Get team data
            team_data = teams_data.get(team_key, {})
            if isinstance(team_data, dict):
                players = team_data.get("players", [])
            else:
                # If team_data is directly a list of players
                players = team_data if isinstance(team_data, list) else []
                # Convert to proper structure
                team_data = {"players": players}
                teams_data[team_key] = team_data
            
            # Create teams structure if it doesn't exist
            if "teams" not in edited_data:
                edited_data["teams"] = {}
            if team_key not in edited_data["teams"]:
                edited_data["teams"][team_key] = {"players": []}
            
            # Ensure players is a list
            if not isinstance(players, list):
                players = []
            
            edit_player_data(team_key, players, edited_data)
        
        elif choice == "4":
            # View current match data
            pretty_print_match(edited_data)
        
        elif choice == "5":
            # Save and exit
            break
        
        else:
            print("Invalid choice, please try again.")
    
    return edited_data

def edit_player_data(team_key, players, edited_data):
    """Edit player data for a specific team"""
    while True:
        print(f"\nEditing {team_key.upper()} team players:")
        print("\nCurrent players:")
        for i, player in enumerate(players):
            if isinstance(player, dict):
                print(f"{i+1}. {player.get('player', 'Unknown')} - Score: {player.get('score', 0)}")
            else:
                print(f"{i+1}. {player}")
        
        print("\nPLAYER EDIT OPTIONS:")
        print("1. Add a new player")
        print("2. Edit an existing player")
        print("3. Remove a player")
        print("4. Return to main edit menu")
        
        choice = input("\nEnter your choice (1-4): ").strip()
        
        if choice == "1":
            # Add a new player
            new_player = create_new_player()
            players.append(new_player)
            
            # Update the match data
            edited_data["teams"][team_key]["players"] = players
        
        elif choice == "2":
            # Edit an existing player
            if not players:
                print("No players to edit.")
                continue
            
            try:
                player_index = int(input("Enter player number to edit: ")) - 1
                if 0 <= player_index < len(players):
                    player = players[player_index]
                    edited_player = edit_player(player)
                    players[player_index] = edited_player
                    
                    # Update the match data
                    edited_data["teams"][team_key]["players"] = players
                else:
                    print("Invalid player number.")
            except ValueError:
                print("Please enter a valid number.")
        
        elif choice == "3":
            # Remove a player
            if not players:
                print("No players to remove.")
                continue
            
            try:
                player_index = int(input("Enter player number to remove: ")) - 1
                if 0 <= player_index < len(players):
                    removed = players.pop(player_index)
                    if isinstance(removed, dict):
                        print(f"Removed player: {removed.get('player', 'Unknown')}")
                    else:
                        print(f"Removed player: {removed}")
                    
                    # Update the match data
                    edited_data["teams"][team_key]["players"] = players
                else:
                    print("Invalid player number.")
            except ValueError:
                print("Please enter a valid number.")
        
        elif choice == "4":
            # Return to main menu
            break
        
        else:
            print("Invalid choice, please try again.")

def create_new_player():
    """Create a new player data dictionary"""
    player = {}
    
    player["player"] = input("Player name: ").strip()
    player["position"] = input("Position (optional): ").strip()
    
    try:
        player["score"] = int(input("Score: ").strip() or "0")
    except ValueError:
        player["score"] = 0
    
    try:
        player["kills"] = int(input("Kills: ").strip() or "0")
    except ValueError:
        player["kills"] = 0
    
    try:
        player["deaths"] = int(input("Deaths: ").strip() or "0")
    except ValueError:
        player["deaths"] = 0
    
    try:
        player["assists"] = int(input("Assists: ").strip() or "0")
    except ValueError:
        player["assists"] = 0
    
    try:
        player["ai_kills"] = int(input("AI Kills: ").strip() or "0")
    except ValueError:
        player["ai_kills"] = 0
    
    try:
        player["cap_ship_damage"] = int(input("Capital Ship Damage: ").strip() or "0")
    except ValueError:
        player["cap_ship_damage"] = 0
    
    return player

def edit_player(player):
    """Edit an existing player data"""
    edited_player = player.copy() if isinstance(player, dict) else {"player": str(player)}
    
    # Default values if not present
    if "position" not in edited_player:
        edited_player["position"] = ""
    if "score" not in edited_player:
        edited_player["score"] = 0
    if "kills" not in edited_player:
        edited_player["kills"] = 0
    if "deaths" not in edited_player:
        edited_player["deaths"] = 0
    if "assists" not in edited_player:
        edited_player["assists"] = 0
    if "ai_kills" not in edited_player:
        edited_player["ai_kills"] = 0
    if "cap_ship_damage" not in edited_player:
        edited_player["cap_ship_damage"] = 0
    
    print("\nEditing player. Press Enter to keep current value.")
    
    name = input(f"Player name [{edited_player.get('player', 'Unknown')}]: ").strip()
    if name:
        edited_player["player"] = name
    
    position = input(f"Position [{edited_player.get('position', '')}]: ").strip()
    if position:
        edited_player["position"] = position
    
    score = input(f"Score [{edited_player.get('score', 0)}]: ").strip()
    if score:
        try:
            edited_player["score"] = int(score)
        except ValueError:
            print("Invalid score value, keeping current value.")
    
    kills = input(f"Kills [{edited_player.get('kills', 0)}]: ").strip()
    if kills:
        try:
            edited_player["kills"] = int(kills)
        except ValueError:
            print("Invalid kills value, keeping current value.")
    
    deaths = input(f"Deaths [{edited_player.get('deaths', 0)}]: ").strip()
    if deaths:
        try:
            edited_player["deaths"] = int(deaths)
        except ValueError:
            print("Invalid deaths value, keeping current value.")
    
    assists = input(f"Assists [{edited_player.get('assists', 0)}]: ").strip()
    if assists:
        try:
            edited_player["assists"] = int(assists)
        except ValueError:
            print("Invalid assists value, keeping current value.")
    
    ai_kills = input(f"AI Kills [{edited_player.get('ai_kills', 0)}]: ").strip()
    if ai_kills:
        try:
            edited_player["ai_kills"] = int(ai_kills)
        except ValueError:
            print("Invalid AI kills value, keeping current value.")
    
    cap_ship_damage = input(f"Capital Ship Damage [{edited_player.get('cap_ship_damage', 0)}]: ").strip()
    if cap_ship_damage:
        try:
            edited_player["cap_ship_damage"] = int(cap_ship_damage)
        except ValueError:
            print("Invalid capital ship damage value, keeping current value.")
    
    return edited_player

def main():
    """Main entry point for the data cleaner utility"""
    parser = argparse.ArgumentParser(description="Clean extracted Star Wars Squadrons match data")
    
    parser.add_argument("--input", type=str, required=True,
                      help="Path to the all_seasons_data.json file")
    parser.add_argument("--output", type=str,
                      help="Path to save the cleaned data file")
    
    args = parser.parse_args()
    
    clean_data(args.input, args.output)

if __name__ == "__main__":
    main()