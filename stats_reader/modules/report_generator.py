"""
Report generation module for Star Wars Squadrons statistics.
Generates various JSON reports from the database.
"""

import os
import json
import sqlite3


def generate_stats_reports(db_path, output_dir):
    """Generate various statistics reports from the database"""
    if not os.path.exists(db_path):
        print(f"Error: Database file not found: {db_path}")
        return False
    
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row  # Enable row factory for named columns
    cursor = conn.cursor()
    
    # 1. Team Standings Report
    cursor.execute("""
    SELECT name, wins, losses, (wins + losses) as games_played, 
            CAST(wins AS FLOAT) / (wins + losses) AS win_rate
    FROM teams
    WHERE (wins + losses) > 0
    ORDER BY win_rate DESC, wins DESC
    """)
    
    team_standings = [dict(row) for row in cursor.fetchall()]
    
    with open(os.path.join(output_dir, "team_standings.json"), 'w') as f:
        json.dump(team_standings, f, indent=2)
    
    # 2. Generate combined reports for all match types (regardless of match_type)
    # --- Player Performance (All) ---
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
    GROUP BY ps.player_hash
    ORDER BY avg_score DESC
    """)
    
    player_performance = [dict(row) for row in cursor.fetchall()]
    with open(os.path.join(output_dir, "player_performance.json"), 'w') as f:
        json.dump(player_performance, f, indent=2)
    
    # --- Player Performance (No Subs) ---
    cursor.execute("""
    SELECT ps.player_name as name, ps.player_hash as hash,
            COUNT(DISTINCT ps.match_id) as games_played,
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
    WHERE ps.is_subbing = 0
    GROUP BY ps.player_hash
    ORDER BY avg_score DESC
    """)
    
    player_performance_no_subs = [dict(row) for row in cursor.fetchall()]
    with open(os.path.join(output_dir, "player_performance_no_subs.json"), 'w') as f:
        json.dump(player_performance_no_subs, f, indent=2)

    # 3. Generate Player Performance Reports per Match Type
    match_types = ['team', 'pickup', 'ranked']
    generated_player_reports = [] # Keep track of generated files

    for mt in match_types:
        # --- Player Performance (All) ---
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
        WHERE m.match_type = ?
        GROUP BY ps.player_hash
        ORDER BY avg_score DESC
        """, (mt,))
        
        player_performance_data = [dict(row) for row in cursor.fetchall()]
        if player_performance_data: # Only write file if data exists for this type
            filename = f"player_performance_{mt}.json"
            filepath = os.path.join(output_dir, filename)
            with open(filepath, 'w') as f:
                json.dump(player_performance_data, f, indent=2)
            generated_player_reports.append(filename)

        # --- Player Performance (No Subs) ---
        # Only generate "no subs" reports for team matches, skip for pickup/ranked
        if mt == 'team':
            cursor.execute("""
            SELECT ps.player_name as name, ps.player_hash as hash,
                    COUNT(DISTINCT ps.match_id) as games_played,
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
            WHERE ps.is_subbing = 0 AND m.match_type = ?
            GROUP BY ps.player_hash
            ORDER BY avg_score DESC
            """, (mt,))

            player_performance_no_subs_data = [dict(row) for row in cursor.fetchall()]
            if player_performance_no_subs_data: # Only write file if data exists
                filename_no_subs = f"player_performance_no_subs_{mt}.json"
                filepath_no_subs = os.path.join(output_dir, filename_no_subs)
                with open(filepath_no_subs, 'w') as f:
                    json.dump(player_performance_no_subs_data, f, indent=2)
                generated_player_reports.append(filename_no_subs)
    
    # 4. Faction Win Rates
    cursor.execute("""
    SELECT winner, COUNT(*) as wins,
            ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM matches WHERE winner != 'UNKNOWN'), 2) as win_percentage
    FROM matches
    WHERE winner != 'UNKNOWN'
    GROUP BY winner
    """)
    
    faction_win_rates = [dict(row) for row in cursor.fetchall()]
    
    with open(os.path.join(output_dir, "faction_win_rates.json"), 'w') as f:
        json.dump(faction_win_rates, f, indent=2)
    
    # 5. Season Summary
    cursor.execute("""
    SELECT s.name as season, 
            COUNT(m.id) as matches_played,
            SUM(CASE WHEN m.winner = 'IMPERIAL' THEN 1 ELSE 0 END) as imperial_wins,
            SUM(CASE WHEN m.winner = 'REBEL' THEN 1 ELSE 0 END) as rebel_wins
    FROM seasons s
    LEFT JOIN matches m ON s.id = m.season_id
    GROUP BY s.id
    ORDER BY s.name
    """)
    
    season_summary = [dict(row) for row in cursor.fetchall()]
    
    with open(os.path.join(output_dir, "season_summary.json"), 'w') as f:
        json.dump(season_summary, f, indent=2)
    
    # 6. Player's Team History - updated to include subbing info
    cursor.execute("""
    SELECT ps.player_name, ps.player_hash, 
            t.name as team_name, 
            COUNT(DISTINCT ps.match_id) as games_with_team,
            SUM(CASE WHEN ps.is_subbing = 0 THEN 1 ELSE 0 END) as regular_games,
            SUM(CASE WHEN ps.is_subbing = 1 THEN 1 ELSE 0 END) as sub_games
    FROM player_stats ps
    JOIN teams t ON ps.team_id = t.id
    GROUP BY ps.player_hash, t.id
    ORDER BY ps.player_name, games_with_team DESC
    """)
    
    player_teams = [dict(row) for row in cursor.fetchall()]
    
    with open(os.path.join(output_dir, "player_teams.json"), 'w') as f:
        json.dump(player_teams, f, indent=2)
    
    # 7. Subbing Report - focusing on substitutes - only for team matches
    cursor.execute("""
    SELECT 
        p.name as player_name,
        t.name as team_name,
        COUNT(DISTINCT ps.match_id) as games_subbed,
        ROUND(AVG(ps.score), 2) as avg_score,
        SUM(ps.kills) as total_kills,
        SUM(ps.deaths) as total_deaths,
        CASE WHEN SUM(ps.deaths) > 0 
            THEN ROUND(CAST(SUM(ps.kills) AS FLOAT) / SUM(ps.deaths), 2)
            ELSE SUM(ps.kills) END as kd_ratio,
        SUM(ps.assists) as total_assists,
        SUM(ps.cap_ship_damage) as total_cap_ship_damage
    FROM player_stats ps
    JOIN players p ON ps.player_id = p.id
    JOIN teams t ON ps.team_id = t.id
    JOIN matches m ON ps.match_id = m.id
    WHERE ps.is_subbing = 1 AND m.match_type = 'team'
    GROUP BY ps.player_id, ps.team_id
    ORDER BY games_subbed DESC, avg_score DESC
    """)
    
    subbing_report = [dict(row) for row in cursor.fetchall()]
    
    with open(os.path.join(output_dir, "subbing_report.json"), 'w') as f:
        json.dump(subbing_report, f, indent=2)
    
    # Print summary of generated reports
    print(f"\nGenerated reports in {output_dir}:")
    print(f"  - Team Standings: {len(team_standings)} teams")
    print(f"  - Player Performance: {len(player_performance)} players")
    print(f"  - Player Performance (No Subs): {len(player_performance_no_subs)} players")
    print("  - Per match type reports:")
    for mt in match_types:
        if mt == 'team':
            for report_name in [f"player_performance_{mt}.json", f"player_performance_no_subs_{mt}.json"]:
                if report_name in generated_player_reports:
                    print(f"    - {report_name}")
        else:
            report_name = f"player_performance_{mt}.json"
            if report_name in generated_player_reports:
                print(f"    - {report_name}")
    print(f"  - Faction Win Rates: {len(faction_win_rates)} factions")
    print(f"  - Season Summary: {len(season_summary)} seasons")
    print(f"  - Player Teams: {len(player_teams)} player-team combinations")
    print(f"  - Subbing Report: {len(subbing_report)} player-team sub combinations")
    
    conn.close()
    return True
