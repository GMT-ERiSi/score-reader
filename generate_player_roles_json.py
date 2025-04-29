"""
Script to generate a consolidated player roles JSON file.
"""

import os
import json
import sqlite3
import sys

def generate_player_roles_json(db_path, output_dir):
    """Generate a JSON file mapping player names/hashes to their primary roles"""
    if not os.path.exists(db_path):
        print(f"Error: Database file not found: {db_path}")
        return False
    
    # Check if output directory exists, create if not
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row  # Enable row factory for named columns
    cursor = conn.cursor()
    
    # First, check if we have role data in the player_stats table
    cursor.execute("SELECT COUNT(*) as count FROM player_stats WHERE role IS NOT NULL")
    role_count = cursor.fetchone()['count']
    
    # Check if we have reference DB for additional role information
    ref_db_path = os.path.join(os.path.dirname(db_path), "squadrons_reference.db")
    has_ref_db = os.path.exists(ref_db_path)
    
    print(f"Found {role_count} player stats records with roles")
    print(f"Reference database exists: {has_ref_db}")
    
    # Dictionary to store player roles {player_name: role, player_hash: role}
    player_roles = {}
    
    # 1. Get roles from player_stats table
    cursor.execute("""
    SELECT 
        ps.player_name, 
        ps.player_hash, 
        ps.role,
        COUNT(*) as appearances
    FROM player_stats ps
    WHERE ps.role IS NOT NULL
    GROUP BY ps.player_name, ps.role
    ORDER BY appearances DESC
    """)
    
    # Get most common role for each player (some players might have multiple roles)
    player_role_counts = {}
    for row in cursor.fetchall():
        player_name = row['player_name']
        player_hash = row['player_hash']
        role = row['role']
        count = row['appearances']
        
        if player_name not in player_role_counts:
            player_role_counts[player_name] = {}
        
        if role not in player_role_counts[player_name]:
            player_role_counts[player_name][role] = 0
        
        player_role_counts[player_name][role] += count
    
    # Assign most frequent role to each player
    for player, role_counts in player_role_counts.items():
        most_frequent_role = max(role_counts.items(), key=lambda x: x[1])[0]
        player_roles[player] = most_frequent_role
    
    # 2. Get roles from reference database if available
    if has_ref_db:
        ref_conn = sqlite3.connect(ref_db_path)
        ref_conn.row_factory = sqlite3.Row
        ref_cursor = ref_conn.cursor()
        
        ref_cursor.execute("""
        SELECT name, primary_role 
        FROM ref_players 
        WHERE primary_role IS NOT NULL
        """)
        
        for row in ref_cursor.fetchall():
            player_name = row['name']
            role = row['primary_role']
            
            # Only add from reference DB if we don't already have a role
            if player_name not in player_roles:
                player_roles[player_name] = role
        
        ref_conn.close()
    
    # 3. Write the roles to JSON
    print(f"Writing roles for {len(player_roles)} players to player_roles.json")
    with open(os.path.join(output_dir, "player_roles.json"), 'w') as f:
        json.dump(player_roles, f, indent=2)
    
    # Display summary
    farmer_count = sum(1 for role in player_roles.values() if role == 'Farmer')
    flex_count = sum(1 for role in player_roles.values() if role == 'Flex')
    support_count = sum(1 for role in player_roles.values() if role == 'Support')
    
    print("\n=== Role Distribution ===")
    print(f"Farmer: {farmer_count} players")
    print(f"Flex: {flex_count} players")
    print(f"Support: {support_count} players")
    print(f"Total: {len(player_roles)} players with roles")
    
    conn.close()
    return True

if __name__ == "__main__":
    db_path = "squadrons_stats_test.db"
    output_dir = "stats_reports_test"
    
    if len(sys.argv) > 1:
        db_path = sys.argv[1]
    if len(sys.argv) > 2:
        output_dir = sys.argv[2]
    
    generate_player_roles_json(db_path, output_dir)
