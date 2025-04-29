/**
 * leaderboardManager.js
 * Handles the creation and management of all leaderboard types
 */

// Import necessary functions from tableInteractivity
import { updateRankNumbersForVisible } from './tableInteractivity.js';

// Helper function to create a new table element with headers
function createLeaderboardTable(id, headers) {
    const table = document.createElement('table');
    table.id = id;
    
    // Create table header
    const thead = document.createElement('thead');
    const headerRow = document.createElement('tr');
    
    headers.forEach(header => {
        const th = document.createElement('th');
        th.textContent = header;
        // Add rank-cell class to the first column if it's "Rank"
        if (header === 'Rank') {
            th.classList.add('rank-cell');
        }
        headerRow.appendChild(th);
    });
    
    thead.appendChild(headerRow);
    table.appendChild(thead);
    
    // Create table body
    const tbody = document.createElement('tbody');
    table.appendChild(tbody);
    
    return table;
}

// Generic function to populate a leaderboard with data
function populateLeaderboard(tableId, data, columns) {
    const tableBody = document.getElementById(tableId)?.querySelector('tbody');
    if (!tableBody) {
        console.warn(`Table body for ID '${tableId}' not found.`);
        return;
    }
    
    // Clear previous content
    tableBody.innerHTML = '';
    
    // Add rows
    data.forEach(item => {
        const row = document.createElement('tr');
        // Add data-role attribute for filtering
        const role = item.role || 'None'; // Use 'None' if role is null/undefined
        row.setAttribute('data-role', role);

        // Add cells based on provided columns configuration
        columns.forEach(column => {
            const cell = document.createElement('td');

            // Handle special formatting or role display
            if (column.format) {
                cell.textContent = column.format(item[column.key]);
            } else if (column.key === 'role') { // Display role nicely
                cell.textContent = item[column.key] || 'None'; // Show 'None' if role is missing
            } else {
                // Ensure we handle potential null/undefined values gracefully
                cell.textContent = item[column.key] !== null && item[column.key] !== undefined ? item[column.key] : '';
            }

            // Add class if specified
            if (column.class) {
                cell.classList.add(column.class);
            }

            row.appendChild(cell);
        });
        
        tableBody.appendChild(row);
    });
}

// Create AI Kills Leaderboard
function createAIKillsLeaderboard(containerId, data) {
    if (!data || data.length === 0) {
        console.warn('No data provided for AI Kills leaderboard');
        return null;
    }
    
    // Sort data by AI kills in descending order
    const sortedData = [...data].sort((a, b) => b.ai_kills - a.ai_kills);
    
    // Add rank property
    sortedData.forEach((item, index) => {
        item.rank = index + 1;
    });
    
    // Define columns for this leaderboard
    const columns = [
        { key: 'rank', class: 'rank-cell' },
        { key: 'player_name' },
        { key: 'role' }, // Add role column
        { key: 'ai_kills' },
        { key: 'matches_played' },
        { key: 'ai_kills_per_match', format: val => (val ? val.toFixed(2) : '0.00') }
    ];

    // Create table
    const tableId = 'aiKillsTable';
    const table = createLeaderboardTable(tableId, [
        'Rank', 'Player', 'Role', 'AI Kills', 'Matches', 'Kills per Match' // Add Role header
    ]);
    
    // Add table to container
    const container = document.getElementById(containerId);
    if (container) {
        container.appendChild(table);
        
        // Populate with data
        populateLeaderboard(tableId, sortedData, columns);
        return tableId;
    }
    
    return null;
}

// Create Damage Leaderboard
function createDamageLeaderboard(containerId, data) {
    if (!data || data.length === 0) {
        console.warn('No data provided for Damage leaderboard');
        return null;
    }
    
    // Sort data by damage in descending order
    const sortedData = [...data].sort((a, b) => b.total_damage - a.total_damage);
    
    // Add rank property
    sortedData.forEach((item, index) => {
        item.rank = index + 1;
    });
    
    // Define columns for this leaderboard
    const columns = [
        { key: 'rank', class: 'rank-cell' },
        { key: 'player_name' },
        { key: 'role' }, // Add role column
        { key: 'total_damage' },
        { key: 'matches_played' },
        { key: 'damage_per_match', format: val => (val ? val.toFixed(0) : '0') }
    ];

    // Create table
    const tableId = 'damageTable';
    const table = createLeaderboardTable(tableId, [
        'Rank', 'Player', 'Role', 'Total Damage', 'Matches', 'Damage per Match' // Add Role header
    ]);
    
    // Add table to container
    const container = document.getElementById(containerId);
    if (container) {
        container.appendChild(table);
        
        // Populate with data
        populateLeaderboard(tableId, sortedData, columns);
        return tableId;
    }
    
    return null;
}

// Create Net Kills Leaderboard
function createNetKillsLeaderboard(containerId, data) {
    if (!data || data.length === 0) {
        console.warn('No data provided for Net Kills leaderboard');
        return null;
    }
    
    // Calculate net kills (player_kills - deaths) and net kills per game
    const processedData = data.map(player => ({
        ...player,
        net_kills: player.player_kills - player.deaths,
        net_kills_per_game: player.matches_played > 0 ? 
            parseFloat(((player.player_kills - player.deaths) / player.matches_played).toFixed(2)) : 0
    }));
    
    // Sort data by net kills in descending order
    const sortedData = [...processedData].sort((a, b) => b.net_kills - a.net_kills);
    
    // Add rank property
    sortedData.forEach((item, index) => {
        item.rank = index + 1;
    });
    
    // Define columns for this leaderboard
    const columns = [
        { key: 'rank', class: 'rank-cell' },
        { key: 'player_name' },
        { key: 'role' }, // Add role column
        { key: 'net_kills' },
        { key: 'net_kills_per_game', format: val => val.toFixed(2) }, // Added net kills per game
        { key: 'player_kills' },
        { key: 'deaths' },
        { key: 'matches_played' }
    ];

    // Create table
    const tableId = 'netKillsTable';
    const table = createLeaderboardTable(tableId, [
        'Rank', 'Player', 'Role', 'Net Kills', 'Net Kills/Game', 'Kills', 'Deaths', 'Matches' // Added Net Kills/Game header
    ]);
    
    // Add table to container
    const container = document.getElementById(containerId);
    if (container) {
        container.appendChild(table);
        
        // Populate with data
        populateLeaderboard(tableId, sortedData, columns);
        return tableId;
    }
    
    return null;
}

// Create Least Deaths Leaderboard
function createLeastDeathsLeaderboard(containerId, data) {
    if (!data || data.length === 0) {
        console.warn('No data provided for Least Deaths leaderboard');
        return null;
    }
    
    // Calculate deaths per match
    const processedData = data.map(player => ({
        ...player,
        deaths_per_match: player.matches_played > 0 ? player.deaths / player.matches_played : 0
    }));
    
    // Sort data by deaths per match in ascending order (least first)
    const sortedData = [...processedData]
        .filter(player => player.matches_played >= 3) // Only include players with at least 3 matches
        .sort((a, b) => a.deaths_per_match - b.deaths_per_match);
    
    // Add rank property
    sortedData.forEach((item, index) => {
        item.rank = index + 1;
    });
    
    // Define columns for this leaderboard
    const columns = [
        { key: 'rank', class: 'rank-cell' },
        { key: 'player_name' },
        { key: 'role' }, // Add role column
        { key: 'deaths' },
        { key: 'matches_played' },
        { key: 'deaths_per_match', format: val => val.toFixed(2) }
    ];

    // Create table
    const tableId = 'leastDeathsTable';
    const table = createLeaderboardTable(tableId, [
        'Rank', 'Player', 'Role', 'Total Deaths', 'Matches', 'Deaths per Match' // Add Role header
    ]);
    
    // Add table to container
    const container = document.getElementById(containerId);
    if (container) {
        container.appendChild(table);
        
        // Populate with data
        populateLeaderboard(tableId, sortedData, columns);
        return tableId;
    }
    
    return null;
}

// Function to create all additional leaderboards
async function createAdditionalLeaderboards(containerSelector, playerStatsData) {
    if (!playerStatsData || playerStatsData.length === 0) {
        console.warn('No player stats data provided for additional leaderboards');
        return;
    }
    
    const container = document.querySelector(containerSelector);
    if (!container) {
        console.warn(`Container '${containerSelector}' not found`);
        return;
    }
    
    // Create section for additional leaderboards
    const section = document.createElement('section');
    section.id = 'additional-leaderboards';
    section.innerHTML = '<h2>Additional Leaderboards</h2>';
    section.style.maxWidth = '1200px';
    section.style.margin = '2rem auto';
    section.style.padding = '1.5rem';
    section.style.backgroundColor = 'rgba(30, 32, 35, 0.8)';
    section.style.borderRadius = '8px';
    section.style.border = '1px solid #444';
    section.style.boxShadow = '0 0 20px rgba(0, 0, 0, 0.5)';
    container.appendChild(section);
    
    try {
        // Dynamically import the tableInteractivity module
        const tableInteractivity = await import('./tableInteractivity.js');
        const { makeTableSortable, addTableFilter } = tableInteractivity;
        
        // Add individual leaderboard sections
        const leaderboardsConfig = [
            {
                title: 'AI Kills Leaderboard',
                id: 'ai-kills-section',
                creatorFunction: createAIKillsLeaderboard
            },
            {
                title: 'Damage Leaderboard',
                id: 'damage-section',
                creatorFunction: createDamageLeaderboard
            },
            {
                title: 'Net Kills Leaderboard',
                id: 'net-kills-section',
                creatorFunction: createNetKillsLeaderboard
            },
            {
                title: 'Least Deaths Leaderboard',
                id: 'least-deaths-section',
                creatorFunction: createLeastDeathsLeaderboard
            }
        ];
        
        // Create each leaderboard
        leaderboardsConfig.forEach(config => {
            const leaderboardSection = document.createElement('div');
            leaderboardSection.className = 'leaderboard-section';
            leaderboardSection.id = config.id;
            
            const heading = document.createElement('h3');
            heading.textContent = config.title;
            leaderboardSection.appendChild(heading);
            
            section.appendChild(leaderboardSection);
            
            // Create the leaderboard table
            const tableId = config.creatorFunction(config.id, playerStatsData);
            
            // Apply interactivity if table was created successfully
            if (tableId) {
                makeTableSortable(tableId);
                // Removed addTableFilter call to be consistent with main tables
            }
        });
        
        return section;
    } catch (error) {
        console.error('Error creating additional leaderboards:', error);
        section.innerHTML += '<p class="error-message">Error loading leaderboards. See console for details.</p>';
    }
}

// Function to filter all leaderboard tables by role
function filterAllLeaderboards(roleFilter) {
    console.log(`Filtering all leaderboards by role: ${roleFilter}`);
    const leaderboardContainer = document.getElementById('additional-leaderboards');
    if (!leaderboardContainer) {
        console.warn('Leaderboard container not found.');
        return;
    }

    // Get all tables in the leaderboard container
    const tables = leaderboardContainer.querySelectorAll('table');
    
    // Special handling for 'all' role - show all rows
    if (roleFilter === 'all') {
        console.log('Showing ALL rows for all tables - All Roles selected');
        tables.forEach(table => {
            const rows = table.querySelectorAll('tbody tr');
            rows.forEach(row => {
                // Make sure to remove any previous display style
                row.style.display = '';
            });
            
            // Update rank numbers for visible rows
            updateRankNumbersForVisible(table);
            
            // Hide any "no results" messages
            const noResultsMsg = table.parentNode.querySelector('.no-results-message');
            if (noResultsMsg) {
                noResultsMsg.style.display = 'none';
            }
            
            console.log(`Reset complete: ${rows.length} rows now visible in table ${table.id}`);
        });
        
        // Special diagnostic log to verify the reset is complete
        console.log('ALL ROLES reset complete!');
        return;
    }
    
    // For other role filters, use the existing logic
    // If we have role-specific data available, use it for filtering
    if (window.roleSpecificData && roleFilter !== 'none') {
        // Generate the data for the specified role
        const roleData = window.roleSpecificData[roleFilter] || [];
        
        if (roleData.length > 0) {
            console.log(`Using ${roleData.length} players from role-specific data for ${roleFilter}`);
            
            // For each table, regenerate content with role-specific data
            tables.forEach(table => {
                const tableId = table.id;
                
                // Process data based on table type
                let processedData = [];
                
                if (tableId === 'aiKillsTable') {
                    // Sort by AI kills
                    processedData = [...roleData].sort((a, b) => (b.total_ai_kills || 0) - (a.total_ai_kills || 0));
                } 
                else if (tableId === 'damageTable') {
                    // Sort by damage
                    processedData = [...roleData].sort((a, b) => (b.total_cap_ship_damage || 0) - (a.total_cap_ship_damage || 0));
                }
                else if (tableId === 'netKillsTable') {
                    // Calculate and sort by net kills
                    processedData = [...roleData].map(player => ({
                        ...player,
                        net_kills: (player.total_kills || 0) - (player.total_deaths || 0),
                        net_kills_per_game: player.games_played > 0 ? 
                            parseFloat(((player.total_kills || 0) - (player.total_deaths || 0)) / player.games_played).toFixed(2) : '0.00',
                        player_kills: player.total_kills,
                        deaths: player.total_deaths
                    })).sort((a, b) => b.net_kills - a.net_kills);
                }
                else if (tableId === 'leastDeathsTable') {
                    // Calculate deaths per match and sort
                    processedData = [...roleData].map(player => ({
                        ...player,
                        deaths: player.total_deaths,
                        deaths_per_match: player.games_played > 0 ? 
                            (player.total_deaths || 0) / player.games_played : 0
                    }))
                    .filter(player => player.games_played >= 3)
                    .sort((a, b) => a.deaths_per_match - b.deaths_per_match);
                }
                
                // Rank the players
                processedData.forEach((player, index) => {
                    player.rank = index + 1;
                    player.player_name = player.name; // Map to the expected field name
                    player.matches_played = player.games_played;
                });
                
                // Get the table body
                const tableBody = table.querySelector('tbody');
                if (tableBody) {
                    // Clear current content
                    tableBody.innerHTML = '';
                    
                    // Re-add rows for this role
                    processedData.forEach(player => {
                        const row = document.createElement('tr');
                        row.setAttribute('data-role', roleFilter);
                        
                        // Add cells appropriate for each table type
                        if (tableId === 'aiKillsTable') {
                            row.innerHTML = `
                                <td class="rank-cell">${player.rank}</td>
                                <td>${player.name}</td>
                                <td>${roleFilter}</td>
                                <td>${player.total_ai_kills || 0}</td>
                                <td>${player.games_played}</td>
                                <td>${player.ai_kills_per_game ? player.ai_kills_per_game.toFixed(2) : '0.00'}</td>
                            `;
                        }
                        else if (tableId === 'damageTable') {
                            row.innerHTML = `
                                <td class="rank-cell">${player.rank}</td>
                                <td>${player.name}</td>
                                <td>${roleFilter}</td>
                                <td>${player.total_cap_ship_damage || 0}</td>
                                <td>${player.games_played}</td>
                                <td>${player.damage_per_game ? player.damage_per_game.toFixed(0) : '0'}</td>
                            `;
                        }
                        else if (tableId === 'netKillsTable') {
                            row.innerHTML = `
                                <td class="rank-cell">${player.rank}</td>
                                <td>${player.name}</td>
                                <td>${roleFilter}</td>
                                <td>${player.net_kills}</td>
                                <td>${player.net_kills_per_game}</td>
                                <td>${player.total_kills || 0}</td>
                                <td>${player.total_deaths || 0}</td>
                                <td>${player.games_played}</td>
                            `;
                        }
                        else if (tableId === 'leastDeathsTable') {
                            row.innerHTML = `
                                <td class="rank-cell">${player.rank}</td>
                                <td>${player.name}</td>
                                <td>${roleFilter}</td>
                                <td>${player.total_deaths || 0}</td>
                                <td>${player.games_played}</td>
                                <td>${player.deaths_per_match.toFixed(2)}</td>
                            `;
                        }
                        
                        tableBody.appendChild(row);
                    });
                    
                    // Add "no results" message if needed
                    if (processedData.length === 0) {
                        let noResultsMsg = table.parentNode.querySelector('.no-results-message');
                        if (!noResultsMsg) {
                            noResultsMsg = document.createElement('p');
                            noResultsMsg.className = 'no-results-message';
                            noResultsMsg.textContent = `No players found for role: ${roleFilter}`;
                            table.parentNode.insertBefore(noResultsMsg, table.nextSibling);
                        }
                        noResultsMsg.style.display = 'block';
                    }
                }
            });
            
            return; // Skip the normal filtering process if we've regenerated the tables
        }
    }
    
    // If we reach here, we're using the normal filter approach (for 'none' filter, or if role data isn't available)
    tables.forEach(table => {
        const rows = table.querySelectorAll('tbody tr');
        let visibleCount = 0;
        
        rows.forEach(row => {
            const rowRole = row.getAttribute('data-role');
            
            if ((roleFilter === 'none' && rowRole.toLowerCase() === 'none') ||
                (rowRole && rowRole.toLowerCase() === roleFilter.toLowerCase())) {
                row.style.display = '';
                visibleCount++;
            } else {
                row.style.display = 'none';
            }
        });
        
        // Update rank numbers for visible rows in this table
        updateRankNumbersForVisible(table);
        
        // Show/hide "no results" message for this table
        let noResultsMsg = table.parentNode.querySelector('.no-results-message');
        if (visibleCount === 0 && roleFilter !== 'all') {
            if (!noResultsMsg) {
                noResultsMsg = document.createElement('p');
                noResultsMsg.className = 'no-results-message';
                noResultsMsg.textContent = 'No matching players found for this role.';
                table.parentNode.insertBefore(noResultsMsg, table.nextSibling);
            }
            noResultsMsg.style.display = 'block';
        } else if (noResultsMsg) {
            noResultsMsg.style.display = 'none';
        }
    });
}

// Export functions
export {
    createAdditionalLeaderboards,
    populateLeaderboard,
    filterAllLeaderboards // Export the new filter function
};