/**
 * leaderboardManager.js
 * Handles the creation and management of all leaderboard types
 */

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
        
        // Add cells based on provided columns configuration
        columns.forEach(column => {
            const cell = document.createElement('td');
            
            // Handle special formatting if needed
            if (column.format) {
                cell.textContent = column.format(item[column.key]);
            } else {
                cell.textContent = item[column.key];
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
        { key: 'ai_kills' },
        { key: 'matches_played' },
        { key: 'ai_kills_per_match', format: val => (val ? val.toFixed(2) : '0.00') }
    ];
    
    // Create table
    const tableId = 'aiKillsTable';
    const table = createLeaderboardTable(tableId, [
        'Rank', 'Player', 'AI Kills', 'Matches', 'Kills per Match'
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
        { key: 'total_damage' },
        { key: 'matches_played' },
        { key: 'damage_per_match', format: val => (val ? val.toFixed(0) : '0') }
    ];
    
    // Create table
    const tableId = 'damageTable';
    const table = createLeaderboardTable(tableId, [
        'Rank', 'Player', 'Total Damage', 'Matches', 'Damage per Match'
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
    
    // Calculate net kills (player_kills - deaths)
    const processedData = data.map(player => ({
        ...player,
        net_kills: player.player_kills - player.deaths
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
        { key: 'net_kills' },
        { key: 'player_kills' },
        { key: 'deaths' },
        { key: 'matches_played' }
    ];
    
    // Create table
    const tableId = 'netKillsTable';
    const table = createLeaderboardTable(tableId, [
        'Rank', 'Player', 'Net Kills', 'Kills', 'Deaths', 'Matches'
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
        { key: 'deaths' },
        { key: 'matches_played' },
        { key: 'deaths_per_match', format: val => val.toFixed(2) }
    ];
    
    // Create table
    const tableId = 'leastDeathsTable';
    const table = createLeaderboardTable(tableId, [
        'Rank', 'Player', 'Total Deaths', 'Matches', 'Deaths per Match'
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
                addTableFilter(tableId, 'Search players...');
            }
        });
        
        return section;
    } catch (error) {
        console.error('Error creating additional leaderboards:', error);
        section.innerHTML += '<p class="error-message">Error loading leaderboards. See console for details.</p>';
    }
}

// Export functions
export {
    createAdditionalLeaderboards,
    populateLeaderboard
};