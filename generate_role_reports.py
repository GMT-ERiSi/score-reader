"""
Script to generate reports with role support.
"""

import os
import json
import sqlite3
import sys

def generate_role_based_reports(conn, output_dir):
    """Generate player performance reports filtered by role"""
    valid_roles = ["Farmer", "Flex", "Support"]
    
    # Check if output directory exists, create if not
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    print("Generating role-based reports...")
    
    for role in valid_roles:
        # Generate player performance report for this role
        cursor = conn.cursor()
        cursor.execute("""
        SELECT ps.player_name as name, ps.player_hash as hash,
                COUNT(DISTINCT ps.match_id) as games_played,
                SUM(CASE WHEN ps.is_subbing = 0 THEN 1 ELSE 0 END) as regular_games,
                SUM(CASE WHEN ps.is_subbing = 1 THEN 1 ELSE 0 END) as sub_games,
                SUM(ps.score) as total_score,
                ROUND(AVG(ps.score), 2) as avg_score,
                SUM(ps.kills) as total_kills,
                SUM(ps.deaths) as total_deaths,
                CASE WHEN COUNT(DISTINCT ps.match_id) > 0 THEN ROUND(CAST(SUM(ps.deaths) AS FLOAT) / COUNT(DISTINCT ps.match_id), 2) ELSE 0 END as deaths_per_game,
                SUM(ps.kills) - SUM(ps.deaths) as net_kills,
                CASE WHEN COUNT(DISTINCT ps.match_id) > 0 THEN ROUND(CAST(SUM(ps.kills) - SUM(ps.deaths) AS FLOAT) / COUNT(DISTINCT ps.match_id), 2) ELSE 0 END as net_kills_per_game,
                CASE WHEN SUM(ps.deaths) > 0 THEN ROUND(CAST(SUM(ps.kills) AS FLOAT) / SUM(ps.deaths), 2) ELSE SUM(ps.kills) END as kd_ratio,
                SUM(ps.assists) as total_assists,
                SUM(ps.ai_kills) as total_ai_kills,
                CASE WHEN COUNT(DISTINCT ps.match_id) > 0 THEN ROUND(CAST(SUM(ps.ai_kills) AS FLOAT) / COUNT(DISTINCT ps.match_id), 2) ELSE 0 END as ai_kills_per_game,
                SUM(ps.cap_ship_damage) as total_cap_ship_damage,
                CASE WHEN COUNT(DISTINCT ps.match_id) > 0 THEN ROUND(CAST(SUM(ps.cap_ship_damage) AS FLOAT) / COUNT(DISTINCT ps.match_id), 2) ELSE 0 END as damage_per_game
        FROM player_stats ps
        JOIN matches m ON ps.match_id = m.id
        WHERE ps.role = ?
        GROUP BY ps.player_hash
        ORDER BY avg_score DESC
        """, (role,))
        
        player_performance_by_role = [dict(row) for row in cursor.fetchall()]
        
        if player_performance_by_role:  # Only write file if there's data
            role_filename = f"player_performance_role_{role.lower()}.json"
            with open(os.path.join(output_dir, role_filename), 'w') as f:
                json.dump(player_performance_by_role, f, indent=2)
            print(f"  - {role} Role Report: {len(player_performance_by_role)} players")
        else:
            print(f"  - {role} Role Report: No data found")
        
        # Also generate match type specific role reports for each match type
        match_types = ['team', 'pickup', 'ranked']
        for mt in match_types:
            cursor.execute("""
            SELECT ps.player_name as name, ps.player_hash as hash,
                    COUNT(DISTINCT ps.match_id) as games_played,
                    SUM(CASE WHEN ps.is_subbing = 0 THEN 1 ELSE 0 END) as regular_games,
                    SUM(CASE WHEN ps.is_subbing = 1 THEN 1 ELSE 0 END) as sub_games,
                    SUM(ps.score) as total_score,
                    ROUND(AVG(ps.score), 2) as avg_score,
                    SUM(ps.kills) as total_kills,
                    SUM(ps.deaths) as total_deaths,
                    CASE WHEN COUNT(DISTINCT ps.match_id) > 0 THEN ROUND(CAST(SUM(ps.deaths) AS FLOAT) / COUNT(DISTINCT ps.match_id), 2) ELSE 0 END as deaths_per_game,
                    SUM(ps.kills) - SUM(ps.deaths) as net_kills,
                    CASE WHEN COUNT(DISTINCT ps.match_id) > 0 THEN ROUND(CAST(SUM(ps.kills) - SUM(ps.deaths) AS FLOAT) / COUNT(DISTINCT ps.match_id), 2) ELSE 0 END as net_kills_per_game,
                    CASE WHEN SUM(ps.deaths) > 0 THEN ROUND(CAST(SUM(ps.kills) AS FLOAT) / SUM(ps.deaths), 2) ELSE SUM(ps.kills) END as kd_ratio,
                    SUM(ps.assists) as total_assists,
                    SUM(ps.ai_kills) as total_ai_kills,
                    CASE WHEN COUNT(DISTINCT ps.match_id) > 0 THEN ROUND(CAST(SUM(ps.ai_kills) AS FLOAT) / COUNT(DISTINCT ps.match_id), 2) ELSE 0 END as ai_kills_per_game,
                    SUM(ps.cap_ship_damage) as total_cap_ship_damage,
                    CASE WHEN COUNT(DISTINCT ps.match_id) > 0 THEN ROUND(CAST(SUM(ps.cap_ship_damage) AS FLOAT) / COUNT(DISTINCT ps.match_id), 2) ELSE 0 END as damage_per_game
            FROM player_stats ps
            JOIN matches m ON ps.match_id = m.id
            WHERE ps.role = ? AND m.match_type = ?
            GROUP BY ps.player_hash
            ORDER BY avg_score DESC
            """, (role, mt))
            
            data = [dict(row) for row in cursor.fetchall()]
            
            if data:  # Only write file if there's data
                filename = f"player_performance_{mt}_role_{role.lower()}.json"
                with open(os.path.join(output_dir, filename), 'w') as f:
                    json.dump(data, f, indent=2)
                print(f"    - {role} Role + {mt.capitalize()} Report: {len(data)} players")

def generate_role_distribution_report(conn, output_dir):
    """Generate a report showing the distribution of roles"""
    cursor = conn.cursor()
    
    # Count players by role across all matches
    cursor.execute("""
    SELECT 
        ps.role, 
        COUNT(DISTINCT ps.player_id) as unique_players,
        COUNT(ps.id) as total_appearances,
        ROUND(AVG(ps.score), 2) as avg_score,
        ROUND(AVG(ps.kills), 2) as avg_kills,
        ROUND(AVG(ps.deaths), 2) as avg_deaths,
        CASE WHEN SUM(ps.deaths) > 0 
            THEN ROUND(CAST(SUM(ps.kills) AS FLOAT) / SUM(ps.deaths), 2)
            ELSE SUM(ps.kills) END as overall_kd_ratio
    FROM player_stats ps
    GROUP BY ps.role
    ORDER BY ps.role
    """)
    
    role_distribution = [dict(row) for row in cursor.fetchall()]
    
    # Count players by role and match type
    cursor.execute("""
    SELECT 
        ps.role,
        m.match_type, 
        COUNT(DISTINCT ps.player_id) as unique_players,
        COUNT(ps.id) as total_appearances,
        ROUND(AVG(ps.score), 2) as avg_score,
        ROUND(AVG(ps.kills), 2) as avg_kills,
        ROUND(AVG(ps.deaths), 2) as avg_deaths,
        CASE WHEN SUM(ps.deaths) > 0 
            THEN ROUND(CAST(SUM(ps.kills) AS FLOAT) / SUM(ps.deaths), 2)
            ELSE SUM(ps.kills) END as overall_kd_ratio
    FROM player_stats ps
    JOIN matches m ON ps.match_id = m.id
    GROUP BY ps.role, m.match_type
    ORDER BY ps.role, m.match_type
    """)
    
    role_distribution_by_match_type = [dict(row) for row in cursor.fetchall()]
    
    # Write reports
    with open(os.path.join(output_dir, "role_distribution.json"), 'w') as f:
        json.dump(role_distribution, f, indent=2)
    
    with open(os.path.join(output_dir, "role_distribution_by_match_type.json"), 'w') as f:
        json.dump(role_distribution_by_match_type, f, indent=2)
    
    print(f"  - Role Distribution: {len(role_distribution)} roles")
    print(f"  - Role Distribution by Match Type: {len(role_distribution_by_match_type)} role-match type combinations")
    
    # Print summary table
    print("\n=== Role Distribution Summary ===")
    print(f"{'Role':12} {'Players':8} {'Appearances':12} {'Avg Score':10} {'K/D Ratio':10}")
    print("-" * 55)
    for row in role_distribution:
        role_name = row['role'] if row['role'] else "None"
        print(f"{role_name:<12} {row['unique_players']:<8} {row['total_appearances']:<12} {row['avg_score']:<10} {row['overall_kd_ratio']:<10}")

def generate_player_team_roles_report(conn, output_dir):
    """Generate a report showing players' teams and roles"""
    cursor = conn.cursor()
    
    cursor.execute("""
    SELECT ps.player_name, ps.player_hash, 
            t.name as team_name, 
            COUNT(DISTINCT ps.match_id) as games_with_team,
            SUM(CASE WHEN ps.is_subbing = 0 THEN 1 ELSE 0 END) as regular_games,
            SUM(CASE WHEN ps.is_subbing = 1 THEN 1 ELSE 0 END) as sub_games,
            ps.role
    FROM player_stats ps
    JOIN teams t ON ps.team_id = t.id
    GROUP BY ps.player_hash, t.id, ps.role
    ORDER BY ps.player_name, games_with_team DESC
    """)
    
    player_teams = [dict(row) for row in cursor.fetchall()]
    
    with open(os.path.join(output_dir, "player_teams_roles.json"), 'w') as f:
        json.dump(player_teams, f, indent=2)
    
    print(f"  - Player Teams and Roles: {len(player_teams)} player-team-role combinations")

def main(db_path, output_dir):
    """Generate all role-based reports"""
    if not os.path.exists(db_path):
        print(f"Error: Database file not found: {db_path}")
        return False
    
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row  # Enable row factory for named columns
    
    # Check if role column exists
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(player_stats)")
    columns = [col[1] for col in cursor.fetchall()]
    
    if 'role' not in columns:
        print("Error: 'role' column not found in player_stats table.")
        print("Please run add_role_columns.py first to add the required columns.")
        conn.close()
        return False
    
    # Generate reports
    print(f"Generating role-based reports from {db_path} to {output_dir}...")
    generate_role_based_reports(conn, output_dir)
    generate_role_distribution_report(conn, output_dir)
    generate_player_team_roles_report(conn, output_dir)
    
    conn.close()
    print("Role-based reports generated successfully!")
    return True

if __name__ == "__main__":
    db_path = "squadrons_stats_test.db"
    output_dir = "stats_reports_test"
    
    if len(sys.argv) > 1:
        db_path = sys.argv[1]
    if len(sys.argv) > 2:
        output_dir = sys.argv[2]
    
    main(db_path, output_dir)
