// realData.js - Load actual data files instead of using dummy data
// Place this in the web_visualizations/js/ directory

/**
 * Functions to load real ELO and stats data from the generated JSON report files
 */

// Load player roles data
async function loadPlayerRoles() {
    try {
        // Load player role data from the main stats_reports directory
        console.log('Attempting to load player roles from ../stats_reports/player_roles.json');
        const response = await fetch('../stats_reports/player_roles.json');
        
        if (!response.ok) {
            console.log(`Failed to load player role data: ${response.status} ${response.statusText}. Role filtering might be unavailable.`);
            return {}; // Return empty object if file not found or error
        }
        
        console.log('Successfully loaded player roles.');
        return await response.json();
    } catch (error) {
        console.error('Error loading player role data:', error);
        return {};
    }
}

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
        console.log('Attempting to load pickup ELO ladder from: ../elo_reports_pickup/pickup_player_elo_ladder.json');
        const response = await fetch('../elo_reports_pickup/pickup_player_elo_ladder.json');
        
        if (!response.ok) {
            console.error(`Failed to load pickup player ELO ladder data: ${response.status} ${response.statusText}`);
            throw new Error(`Failed to load pickup player ELO ladder data: ${response.status} ${response.statusText}`);
        }
        
        const data = await response.json();
        console.log(`Successfully loaded pickup ELO ladder with ${data.length} players`);
        return data;
    } catch (error) {
        console.error('Error loading pickup player ELO ladder:', error);
        return [];
    }
}

// Load pickup player ELO history data
async function loadPickupEloHistory() {
    try {
        console.log('Attempting to load pickup ELO history from: ../elo_reports_pickup/pickup_player_elo_history.json');
        const response = await fetch('../elo_reports_pickup/pickup_player_elo_history.json');
        
        if (!response.ok) {
            console.error(`Failed to load pickup player ELO history data: ${response.status} ${response.statusText}`);
            throw new Error(`Failed to load pickup player ELO history data: ${response.status} ${response.statusText}`);
        }
        
        const data = await response.json();
        console.log(`Successfully loaded pickup ELO history with ${data.length} entries`);
        return data;
    } catch (error) {
        console.error('Error loading pickup player ELO history:', error);
        return [];
    }
}

// Load player performance data (for additional leaderboards)
async function loadPlayerStats() {
    try {
        // First check if we're on the pickup page or team page
        const isPickupPage = window.location.href.includes('pickup') || 
                           document.title.toLowerCase().includes('pickup');
        const isTeamPage = window.location.href.includes('team') || 
                           document.title.toLowerCase().includes('team');
        
        console.log(`Page type detection: Pickup Page = ${isPickupPage}, Team Page = ${isTeamPage}`);
        
        if (isPickupPage) {
            console.log('Loading pickup-specific player performance data...');
            
            // Try to load pickup-specific player performance data files
            const pickupFiles = [
                '../elo_reports_pickup/player_performance_pickup.json',
                '../elo_reports_pickup/player_performance_pickup_role_flex.json',
                '../elo_reports_pickup/player_performance_pickup_role_farmer.json',
                '../elo_reports_pickup/player_performance_pickup_role_support.json',
                '../elo_reports_pickup/player_performance_role_flex.json'
            ];
            
            // Try each file until one succeeds
            for (const file of pickupFiles) {
                try {
                    const response = await fetch(file);
                    if (response.ok) {
                        console.log(`Successfully loaded pickup data from: ${file}`);
                        return await response.json();
                    }
                } catch (err) {
                    console.log(`Failed to load ${file}: ${err.message}`);
                }
            }
            
            console.log('No pickup-specific performance data found, falling back to general data');
        }
        else if (isTeamPage) {
            console.log('Loading team-specific player performance data...');
            
            // Define the team-specific role performance files
            const teamRoleFiles = [
                '../stats_reports/player_performance_team_role_farmer.json',
                '../stats_reports/player_performance_team_role_flex.json',
                '../stats_reports/player_performance_team_role_support.json'
                // Add other roles if necessary
            ];

            let combinedTeamStats = [];
            const promises = teamRoleFiles.map(file =>
                fetch(file)
                    .then(response => {
                        if (response.ok) {
                            console.log(`Successfully loaded team role data from: ${file}`);
                            return response.json();
                        }
                        console.log(`File not found or error loading: ${file}`);
                        return null; // Return null for failed fetches
                    })
                    .catch(err => {
                        console.error(`Error fetching ${file}:`, err);
                        return null; // Return null on error
                    })
            );

            const results = await Promise.all(promises);

            results.forEach(data => {
                if (data) {
                    combinedTeamStats = combinedTeamStats.concat(data);
                }
            });

            if (combinedTeamStats.length > 0) {
                console.log(`Successfully combined ${combinedTeamStats.length} player stats entries from team role files.`);
                return combinedTeamStats;
            }

            // If still no data, log an error and proceed to general fallbacks
            console.log('Could not load any team-specific role performance files.');
        }
        
        // If page-specific loading failed or wasn't applicable, try general fallbacks
        console.log('Attempting general fallback performance data load...');
        
        // Try legacy combined file (which likely doesn't exist based on user feedback)
        try {
            const legacyResponse = await fetch('../stats_reports/player_performance.json');
            if (legacyResponse.ok) {
                console.log('Successfully loaded legacy combined performance data');
                return await legacyResponse.json();
            }
        } catch (err) {
            console.log(`Failed to load legacy combined performance data: ${err.message}`);
        }

        // Last resort - return empty array
        console.error('All attempts to load player performance data failed');
        return [];

    } catch (error) {
        console.error('Error loading player performance data:', error);
        return [];
    }
}

// Function to load all real data
async function loadAllRealData() {
    console.log('Loading real data from report files...');
    
    // Load all data in parallel
    const [teamLadder, teamHistory, pickupLadder, pickupHistory, playerPerformance, playerRoles] = await Promise.all([
        loadTeamEloLadder(),
        loadTeamEloHistory(),
        loadPickupEloLadder(),
        loadPickupEloHistory(),
        loadPlayerStats(),
        loadPlayerRoles()
    ]);
    
    console.log('Real data loaded successfully');
    console.log('First 3 player performance records:', playerPerformance.slice(0, 3));
    console.log('Player roles loaded:', Object.keys(playerRoles).length);
    
    // Process player performance data for additional leaderboards
    const processedPlayerStats = playerPerformance.map(player => {
        const result = {
            player_id: player.player_hash || player.hash, // Use hash as ID (accommodate different field names)
            player_name: player.name || player.player_name, // Handle different field names
            role: player.role || playerRoles[player.name || player.player_name] || null, // Add role from the roles data
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
    
    // Also add roles to pickup ladder if they're not already there
    const pickupLadderWithRoles = pickupLadder.map(player => {
        // Log some debug info about player roles
        if (player.player_id <= 5) {
            console.log(`Player ${player.player_name} has role: ${player.role || 'none'} in JSON`);
            console.log(`Player ${player.player_name} has role in playerRoles: ${playerRoles[player.player_name] || 'none'}`);
        }
        
        // Make sure we always have a role property (never undefined)
        if (!player.role && playerRoles[player.player_name]) {
            return {
                ...player,
                role: playerRoles[player.player_name]
            };
        } else if (!player.role) {
            return {
                ...player,
                role: null // Ensure role is null instead of undefined
            };
        }
        return player;
    });
    
    console.log("First few players with roles:", pickupLadderWithRoles.slice(0, 3));
    
    console.log('First 3 processed player stats:', processedPlayerStats.slice(0, 3));
    
    return {
        teamEloLadder: teamLadder,
        teamEloHistory: teamHistory,
        pickupEloLadder: pickupLadderWithRoles,
        pickupEloHistory: pickupHistory,
        playerStats: processedPlayerStats,
        playerRoles: playerRoles
    };
}

export { loadAllRealData };