// realData.js - Load actual data files instead of using dummy data
// Place this in the web_visualizations/js/ directory

/**
 * Functions to load real ELO and stats data from the generated JSON report files
 */

// Load team ELO ladder data
async function loadTeamEloLadder() {
    try {
        // Try to load team ELO ladder data with team match type
        const response = await fetch('../stats_reports/elo_ladder_team.json');
        
        if (!response.ok) {
            // Fall back to legacy filename if team-specific file isn't found
            console.log('Team ELO ladder file not found, trying legacy filename...');
            const legacyResponse = await fetch('../stats_reports/elo_ladder.json');
            
            if (!legacyResponse.ok) {
                throw new Error(`Failed to load team ELO ladder data: ${legacyResponse.status} ${legacyResponse.statusText}`);
            }
            
            return await legacyResponse.json();
        }
        
        return await response.json();
    } catch (error) {
        console.error('Error loading team ELO ladder:', error);
        return [];
    }
}

// Load team ELO history data
async function loadTeamEloHistory() {
    try {
        // Try to load team ELO history data with team match type
        const response = await fetch('../stats_reports/elo_history_team.json');
        
        if (!response.ok) {
            // Fall back to legacy filename if team-specific file isn't found
            console.log('Team ELO history file not found, trying legacy filename...');
            const legacyResponse = await fetch('../stats_reports/elo_history.json');
            
            if (!legacyResponse.ok) {
                throw new Error(`Failed to load team ELO history data: ${legacyResponse.status} ${legacyResponse.statusText}`);
            }
            
            return await legacyResponse.json();
        }
        
        return await response.json();
    } catch (error) {
        console.error('Error loading team ELO history:', error);
        return [];
    }
}

// Load pickup player ELO ladder data
async function loadPickupEloLadder() {
    try {
        const response = await fetch('../elo_reports_pickup/pickup_player_elo_ladder.json');
        
        if (!response.ok) {
            throw new Error(`Failed to load pickup player ELO ladder data: ${response.status} ${response.statusText}`);
        }
        
        return await response.json();
    } catch (error) {
        console.error('Error loading pickup player ELO ladder:', error);
        return [];
    }
}

// Load pickup player ELO history data
async function loadPickupEloHistory() {
    try {
        const response = await fetch('../elo_reports_pickup/pickup_player_elo_history.json');
        
        if (!response.ok) {
            throw new Error(`Failed to load pickup player ELO history data: ${response.status} ${response.statusText}`);
        }
        
        return await response.json();
    } catch (error) {
        console.error('Error loading pickup player ELO history:', error);
        return [];
    }
}

// Load player performance data (for additional leaderboards)
async function loadPlayerStats() {
    try {
        // Try to load team-specific player performance data first
        const response = await fetch('../stats_reports/player_performance_team.json');
        
        if (!response.ok) {
            // Fall back to combined player performance data
            console.log('Team player performance file not found, trying combined performance data...');
            const legacyResponse = await fetch('../stats_reports/player_performance.json');
            
            if (!legacyResponse.ok) {
                throw new Error(`Failed to load player performance data: ${legacyResponse.status} ${legacyResponse.statusText}`);
            }
            
            return await legacyResponse.json();
        }
        
        return await response.json();
    } catch (error) {
        console.error('Error loading player performance data:', error);
        return [];
    }
}

// Function to load all real data
async function loadAllRealData() {
    console.log('Loading real data from report files...');
    
    // Load all data in parallel
    const [teamLadder, teamHistory, pickupLadder, pickupHistory, playerPerformance] = await Promise.all([
        loadTeamEloLadder(),
        loadTeamEloHistory(),
        loadPickupEloLadder(),
        loadPickupEloHistory(),
        loadPlayerStats()
    ]);
    
    console.log('Real data loaded successfully');
    console.log('First 3 player performance records:', playerPerformance.slice(0, 3));
    
    // Process player performance data for additional leaderboards
    const processedPlayerStats = playerPerformance.map(player => {
        const result = {
            player_id: player.player_hash, // Use hash as ID
            player_name: player.name,
            matches_played: player.games_played || 0,
            ai_kills: player.total_ai_kills || 0,
            player_kills: player.total_kills || 0,
            deaths: player.total_deaths || 0,
            total_damage: player.total_cap_ship_damage || 0,
            ai_kills_per_match: player.ai_kills_per_game || 0,
            damage_per_match: player.damage_per_game || 0
        };
        return result;
    });
    
    console.log('First 3 processed player stats:', processedPlayerStats.slice(0, 3));
    
    return {
        teamEloLadder: teamLadder,
        teamEloHistory: teamHistory,
        pickupEloLadder: pickupLadder,
        pickupEloHistory: pickupHistory,
        playerStats: processedPlayerStats
    };
}

export { loadAllRealData };