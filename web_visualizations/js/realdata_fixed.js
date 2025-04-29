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

// Load flex ELO ladder data
async function loadFlexEloLadder() {
    try {
        console.log('Attempting to load flex ELO ladder from: ../elo_reports_pickup/pickup_flex_elo_ladder.json');
        const response = await fetch('../elo_reports_pickup/pickup_flex_elo_ladder.json');
        
        if (!response.ok) {
            console.error(`Failed to load flex ELO ladder data: ${response.status} ${response.statusText}`);
            return [];
        }
        
        const data = await response.json();
        console.log(`Successfully loaded flex ELO ladder with ${data.length} players`);
        return data;
    } catch (error) {
        console.error('Error loading flex ELO ladder:', error);
        return [];
    }
}

// Load support ELO ladder data
async function loadSupportEloLadder() {
    try {
        console.log('Attempting to load support ELO ladder from: ../elo_reports_pickup/pickup_support_elo_ladder.json');
        const response = await fetch('../elo_reports_pickup/pickup_support_elo_ladder.json');
        
        if (!response.ok) {
            console.error(`Failed to load support ELO ladder data: ${response.status} ${response.statusText}`);
            return [];
        }
        
        const data = await response.json();
        console.log(`Successfully loaded support ELO ladder with ${data.length} players`);
        return data;
    } catch (error) {
        console.error('Error loading support ELO ladder:', error);
        return [];
    }
}

// Load farmer ELO ladder data
async function loadFarmerEloLadder() {
    try {
        console.log('Attempting to load farmer ELO ladder from: ../elo_reports_pickup/pickup_farmer_elo_ladder.json');
        const response = await fetch('../elo_reports_pickup/pickup_farmer_elo_ladder.json');
        
        if (!response.ok) {
            console.error(`Failed to load farmer ELO ladder data: ${response.status} ${response.statusText}`);
            return [];
        }
        
        const data = await response.json();
        console.log(`Successfully loaded farmer ELO ladder with ${data.length} players`);
        return data;
    } catch (error) {
        console.error('Error loading farmer ELO ladder:', error);
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
        
        let roleSpecificData = {}; // Will contain data separated by role
        let allRolesCombined = []; // Will contain combined player stats across all roles
        
        if (isPickupPage) {
            console.log('Loading pickup-specific player performance data...');
            
            // Try to load pickup-specific player performance data files
            const pickupFiles = {
                'Flex': ['../elo_reports_pickup/player_performance_pickup_role_flex.json', '../elo_reports_pickup/player_performance_role_flex.json'],
                'Farmer': ['../elo_reports_pickup/player_performance_pickup_role_farmer.json', '../elo_reports_pickup/player_performance_role_farmer.json'],
                'Support': ['../elo_reports_pickup/player_performance_pickup_role_support.json', '../elo_reports_pickup/player_performance_role_support.json']
            };
            
            // Initialize role data containers
            roleSpecificData = {
                'Flex': [],
                'Farmer': [],
                'Support': [],
                'None': []
            };
            
            // Load each role's files
            for (const [role, files] of Object.entries(pickupFiles)) {
                for (const file of files) {
                    try {
                        const response = await fetch(file);
                        if (response.ok) {
                            const data = await response.json();
                            console.log(`Successfully loaded pickup data from: ${file} with ${data.length} players`);
                            
                            // Add role property if not present and store by role
                            data.forEach(player => {
                                player.role = role; // Ensure role is set explicitly
                                // Deduplicate within the same role
                                const existingIndex = roleSpecificData[role].findIndex(p => p.hash === player.hash);
                                if (existingIndex === -1) {
                                    roleSpecificData[role].push(player);
                                } else if (player.games_played > roleSpecificData[role][existingIndex].games_played) {
                                    // Keep the entry with more games played for this role
                                    roleSpecificData[role][existingIndex] = player;
                                }
                            });
                        }
                    } catch (err) {
                        console.log(`Failed to load ${file}: ${err.message}`);
                    }
                }
            }
            
            // For "All" view, combine stats across roles for each player
            const playerMap = {}; // Map to track combined stats by player hash
            
            // Process each role
            Object.entries(roleSpecificData).forEach(([role, players]) => {
                players.forEach(player => {
                    const hash = player.hash;
                    
                    if (!playerMap[hash]) {
                        // First time seeing this player, initialize
                        playerMap[hash] = {
                            name: player.name,
                            hash: player.hash,
                            roles: [], // Track all roles this player has
                            games_played: 0,
                            regular_games: 0,
                            sub_games: 0,
                            total_score: 0,
                            total_kills: 0,
                            total_deaths: 0,
                            total_assists: 0,
                            total_ai_kills: 0,
                            total_cap_ship_damage: 0
                        };
                    }
                    
                    // Combine stats
                    const combinedPlayer = playerMap[hash];
                    combinedPlayer.games_played += player.games_played || 0;
                    combinedPlayer.regular_games += player.regular_games || 0;
                    combinedPlayer.sub_games += player.sub_games || 0;
                    combinedPlayer.total_score += player.total_score || 0;
                    combinedPlayer.total_kills += player.total_kills || 0;
                    combinedPlayer.total_deaths += player.total_deaths || 0;
                    combinedPlayer.total_assists += player.total_assists || 0;
                    combinedPlayer.total_ai_kills += player.total_ai_kills || 0;
                    combinedPlayer.total_cap_ship_damage += player.total_cap_ship_damage || 0;
                    
                    // Track roles
                    if (role !== 'None' && !combinedPlayer.roles.includes(role)) {
                        combinedPlayer.roles.push(role);
                    }
                });
            });
            
            // Calculate averages for combined stats
            Object.values(playerMap).forEach(player => {
                // Set primary role as the first in the roles array
                player.role = player.roles.length > 0 ? player.roles[0] : null;
                
                // Calculate averages for combined stats
                player.avg_score = player.games_played > 0 ? Math.round((player.total_score / player.games_played) * 100) / 100 : 0;
                player.deaths_per_game = player.games_played > 0 ? Math.round((player.total_deaths / player.games_played) * 100) / 100 : 0;
                player.net_kills = player.total_kills - player.total_deaths;
                player.net_kills_per_game = player.games_played > 0 ? Math.round((player.net_kills / player.games_played) * 100) / 100 : 0;
                player.kd_ratio = player.total_deaths > 0 ? Math.round((player.total_kills / player.total_deaths) * 100) / 100 : player.total_kills;
                player.ai_kills_per_game = player.games_played > 0 ? Math.round((player.total_ai_kills / player.games_played) * 100) / 100 : 0;
                player.damage_per_game = player.games_played > 0 ? Math.round(player.total_cap_ship_damage / player.games_played) : 0;
            });
            
            // Convert to array
            allRolesCombined = Object.values(playerMap);
            
            // Log stats for debugging
            console.log(`Loaded: Flex ${roleSpecificData.Flex.length}, Farmer ${roleSpecificData.Farmer.length}, Support ${roleSpecificData.Support.length} players`);
            console.log(`Combined into ${allRolesCombined.length} unique players with role-specific data preserved`);
        }
        else if (isTeamPage) {
            console.log('Loading team-specific player performance data...');
            
            // Define the team-specific role performance files
            const teamRoleFiles = {
                'Flex': ['../stats_reports/player_performance_team_role_flex.json'],
                'Farmer': ['../stats_reports/player_performance_team_role_farmer.json'],
                'Support': ['../stats_reports/player_performance_team_role_support.json']
            };
            
            // Initialize role data containers
            roleSpecificData = {
                'Flex': [],
                'Farmer': [],
                'Support': [],
                'None': []
            };
            
            // Load each role's files
            for (const [role, files] of Object.entries(teamRoleFiles)) {
                for (const file of files) {
                    try {
                        const response = await fetch(file);
                        if (response.ok) {
                            const data = await response.json();
                            console.log(`Successfully loaded team data from: ${file} with ${data.length} players`);
                            
                            // Add role property if not present and store by role
                            data.forEach(player => {
                                player.role = role; // Ensure role is set explicitly
                                // Deduplicate within the same role
                                const existingIndex = roleSpecificData[role].findIndex(p => p.hash === player.hash);
                                if (existingIndex === -1) {
                                    roleSpecificData[role].push(player);
                                } else if (player.games_played > roleSpecificData[role][existingIndex].games_played) {
                                    // Keep the entry with more games played for this role
                                    roleSpecificData[role][existingIndex] = player;
                                }
                            });
                        }
                    } catch (err) {
                        console.log(`Failed to load ${file}: ${err.message}`);
                    }
                }
            }
            
            // For "All" view, combine stats across roles for each player
            const playerMap = {}; // Map to track combined stats by player hash
            
            // Process each role
            Object.entries(roleSpecificData).forEach(([role, players]) => {
                players.forEach(player => {
                    const hash = player.hash;
                    
                    if (!playerMap[hash]) {
                        // First time seeing this player, initialize
                        playerMap[hash] = {
                            name: player.name,
                            hash: player.hash,
                            roles: [], // Track all roles this player has
                            games_played: 0,
                            regular_games: 0,
                            sub_games: 0,
                            total_score: 0,
                            total_kills: 0,
                            total_deaths: 0,
                            total_assists: 0,
                            total_ai_kills: 0,
                            total_cap_ship_damage: 0
                        };
                    }
                    
                    // Combine stats
                    const combinedPlayer = playerMap[hash];
                    combinedPlayer.games_played += player.games_played || 0;
                    combinedPlayer.regular_games += player.regular_games || 0;
                    combinedPlayer.sub_games += player.sub_games || 0;
                    combinedPlayer.total_score += player.total_score || 0;
                    combinedPlayer.total_kills += player.total_kills || 0;
                    combinedPlayer.total_deaths += player.total_deaths || 0;
                    combinedPlayer.total_assists += player.total_assists || 0;
                    combinedPlayer.total_ai_kills += player.total_ai_kills || 0;
                    combinedPlayer.total_cap_ship_damage += player.total_cap_ship_damage || 0;
                    
                    // Track roles
                    if (role !== 'None' && !combinedPlayer.roles.includes(role)) {
                        combinedPlayer.roles.push(role);
                    }
                });
            });
            
            // Calculate averages for combined stats
            Object.values(playerMap).forEach(player => {
                // Set primary role as the first in the roles array
                player.role = player.roles.length > 0 ? player.roles[0] : null;
                
                // Calculate averages for combined stats
                player.avg_score = player.games_played > 0 ? Math.round((player.total_score / player.games_played) * 100) / 100 : 0;
                player.deaths_per_game = player.games_played > 0 ? Math.round((player.total_deaths / player.games_played) * 100) / 100 : 0;
                player.net_kills = player.total_kills - player.total_deaths;
                player.net_kills_per_game = player.games_played > 0 ? Math.round((player.net_kills / player.games_played) * 100) / 100 : 0;
                player.kd_ratio = player.total_deaths > 0 ? Math.round((player.total_kills / player.total_deaths) * 100) / 100 : player.total_kills;
                player.ai_kills_per_game = player.games_played > 0 ? Math.round((player.total_ai_kills / player.games_played) * 100) / 100 : 0;
                player.damage_per_game = player.games_played > 0 ? Math.round(player.total_cap_ship_damage / player.games_played) : 0;
            });
            
            // Convert to array
            allRolesCombined = Object.values(playerMap);
            
            // Log stats for debugging
            console.log(`Loaded: Flex ${roleSpecificData.Flex.length}, Farmer ${roleSpecificData.Farmer.length}, Support ${roleSpecificData.Support.length} players`);
            console.log(`Combined into ${allRolesCombined.length} unique players with role-specific data preserved`);
        }
        
        // Store role-specific data in the window object for access by the filter
        window.roleSpecificData = roleSpecificData;
        
        // Return the combined stats by default
        return allRolesCombined;
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
    const mappedPlayerStats = playerPerformance.map(player => {
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
    
    // Deduplicate players by player_id
    const uniquePlayers = {};
    mappedPlayerStats.forEach(player => {
        if (!uniquePlayers[player.player_id] || uniquePlayers[player.player_id].matches_played < player.matches_played) {
            uniquePlayers[player.player_id] = player;
        }
    });
    
    const processedPlayerStats = Object.values(uniquePlayers);
    console.log(`Deduplicated player stats from ${mappedPlayerStats.length} to ${processedPlayerStats.length} unique players`);
    
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
        playerRoles: playerRoles,
        flexEloLadder: await loadFlexEloLadder(),    
        supportEloLadder: await loadSupportEloLadder(), 
        farmerEloLadder: await loadFarmerEloLadder()  
    };
}

export { loadAllRealData };