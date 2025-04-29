// Debug information
console.log('Script.js loading...');

// Import our modular components
try {
    const moduleStart = performance.now();
    console.log('Importing modules...');

    // Dynamic imports instead of static imports at the top level
    async function loadModules() {
        try {
            console.log('Loading tableInteractivity.js...');
            const tableInteractivity = await import('./js/tableInteractivity.js');
            const { makeTableSortable, addTableFilter, enableTableRowSelection, addRoleFilter, filterTableByRole } = tableInteractivity;
            console.log('tableInteractivity.js loaded successfully');

            console.log('Loading chartInteractivity.js...');
            const chartInteractivity = await import('./js/chartInteractivity.js');
            const { enhanceChartInteractivity, filterChartByName, addChartControls } = chartInteractivity;
            console.log('chartInteractivity.js loaded successfully');

            console.log('Loading leaderboardManager.js...');
            const leaderboardManager = await import('./js/leaderboardManager.js');
            const { createAdditionalLeaderboards } = leaderboardManager;
            console.log('leaderboardManager.js loaded successfully');

            console.log('Loading dataMock.js...');
            const dataMock = await import('./js/dataMock.js');
            const { generateDummyPlayerStats } = dataMock;
            console.log('dataMock.js loaded successfully');

            const moduleEnd = performance.now();
            console.log(`All modules loaded in ${(moduleEnd - moduleStart).toFixed(2)}ms`);

            // Now that modules are loaded, initialize the app
            initializeApp({
                makeTableSortable, 
                addTableFilter, 
                enableTableRowSelection,
                enhanceChartInteractivity,
                filterChartByName,
                addChartControls,
                createAdditionalLeaderboards,
                generateDummyPlayerStats,
                addRoleFilter,
                filterTableByRole
            });

        } catch (error) {
            console.error('Error loading modules:', error);
            document.body.innerHTML += `<div style="color: red; padding: 20px; margin: 20px; border: 1px solid red; background: #ffeeee;">
                <h2>Error Loading Visualization</h2>
                <p>There was an error loading the visualization components. Please check the console for details.</p>
                <p>Error: ${error.message}</p>
            </div>`;
        }
    }

    // Start loading modules
    loadModules();

} catch (error) {
    console.error('Critical error in script.js:', error);
}

// Initialize application with imported modules
function initializeApp(modules) {
    console.log('Initializing application...');
    
    const {
        makeTableSortable, 
        addTableFilter, 
        enableTableRowSelection,
        enhanceChartInteractivity,
        filterChartByName,
        addChartControls,
        createAdditionalLeaderboards,
        generateDummyPlayerStats,
        addRoleFilter,
        filterTableByRole
    } = modules;

    // --- Dummy Data Generation ---
    const k_factor = 32; // Standard K-factor

    // --- Team Data Generation ---
    let dummyTeamEloLadder = [];
    let dummyTeamEloHistory = [];
    let team_ratings = { 1: 1000, 2: 1000, 3: 1000, 4: 1000 }; // Alpha, Bravo, Charlie, Delta
    const team_names = { 1: "Team Alpha", 2: "Team Bravo", 3: "Team Charlie", 4: "Team Delta" };
    let team_stats = {
        1: { played: 0, won: 0, lost: 0 }, 2: { played: 0, won: 0, lost: 0 },
        3: { played: 0, won: 0, lost: 0 }, 4: { played: 0, won: 0, lost: 0 }
    };

    // Simulate 10 team matches with varied outcomes
    const team_matches = [
        { imp: 1, reb: 2, winner: 'IMPERIAL' }, // Alpha wins
        { imp: 3, reb: 4, winner: 'IMPERIAL' }, // Charlie wins
        { imp: 1, reb: 3, winner: 'IMPERIAL' }, // Alpha wins
        { imp: 2, reb: 4, winner: 'IMPERIAL' }, // Bravo wins
        { imp: 1, reb: 4, winner: 'IMPERIAL' }, // Alpha wins
        { imp: 2, reb: 3, winner: 'REBEL' },    // Charlie wins
        { imp: 1, reb: 2, winner: 'REBEL' },    // Bravo wins
        { imp: 3, reb: 4, winner: 'IMPERIAL' }, // Charlie wins
        { imp: 1, reb: 3, winner: 'IMPERIAL' }, // Alpha wins
        { imp: 2, reb: 4, winner: 'IMPERIAL' }  // Bravo wins
    ];

    team_matches.forEach((match, index) => {
        const match_id = 101 + index;
        const match_date = `2024-04-${String(index + 1).padStart(2, '0')} 10:00:00`;
        const imp_id = match.imp;
        const reb_id = match.reb;

        let imp_r = team_ratings[imp_id];
        let reb_r = team_ratings[reb_id];

        let imp_expected = 1.0 / (1.0 + 10 ** ((reb_r - imp_r) / 400));
        let reb_expected = 1.0 - imp_expected;

        let imp_actual = (match.winner === 'IMPERIAL') ? 1.0 : 0.0;
        let reb_actual = (match.winner === 'REBEL') ? 1.0 : 0.0;

        let new_imp_r = imp_r + k_factor * (imp_actual - imp_expected);
        let new_reb_r = reb_r + k_factor * (reb_actual - reb_expected);

        dummyTeamEloHistory.push({
            match_id: match_id, match_date: match_date, season: "DUMMY_TEAM",
            imperial: { team_id: imp_id, team_name: team_names[imp_id], old_rating: imp_r, new_rating: new_imp_r, rating_change: new_imp_r - imp_r },
            rebel: { team_id: reb_id, team_name: team_names[reb_id], old_rating: reb_r, new_rating: new_reb_r, rating_change: new_reb_r - reb_r },
            winner: match.winner
        });

        team_ratings[imp_id] = new_imp_r;
        team_ratings[reb_id] = new_reb_r;

        team_stats[imp_id].played++;
        team_stats[reb_id].played++;
        if (match.winner === 'IMPERIAL') {
            team_stats[imp_id].won++;
            team_stats[reb_id].lost++;
        } else {
            team_stats[reb_id].won++;
            team_stats[imp_id].lost++;
        }
    });

    // Generate final team ladder
    dummyTeamEloLadder = Object.keys(team_ratings).map(id_str => {
        const id = parseInt(id_str);
        const stats = team_stats[id];
        const win_rate = stats.played > 0 ? Math.round((stats.won / stats.played) * 1000) / 10 : 0;
        return {
            team_id: id, team_name: team_names[id], elo_rating: Math.round(team_ratings[id]),
            matches_played: stats.played, matches_won: stats.won, matches_lost: stats.lost, win_rate: win_rate
        };
    });
    dummyTeamEloLadder.sort((a, b) => b.elo_rating - a.elo_rating);
    dummyTeamEloLadder.forEach((t, index) => t.rank = index + 1);

// --- Pickup Player Data Generation ---
let dummyPickupEloLadder = [];
let dummyPickupEloHistory = [];
let p_ratings = { 1: 1000, 2: 1000, 3: 1000, 4: 1000, 5: 1000, 6: 1000, 7: 1000, 8: 1000, 9: 1000, 10: 1000 };
let p_stats = {};
for (let i = 1; i <= 10; i++) { p_stats[i] = { played: 0, won: 0, lost: 0 }; }

// Helper function to shuffle an array (Fisher-Yates algorithm)
function shuffleArray(array) {
    for (let i = array.length - 1; i > 0; i--) {
        const j = Math.floor(Math.random() * (i + 1));
        [array[i], array[j]] = [array[j], array[i]]; // Swap elements
    }
}

// Simulate 10 pickup matches with shuffled teams
const all_player_ids = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10];

for (let i = 1; i <= 10; i++) {
    const match_id = 201 + i;
    const match_date = `2024-04-${String(i).padStart(2, '0')} 15:00:00`;

    // Shuffle players for this match
    shuffleArray(all_player_ids);
    const imp_players_ids = all_player_ids.slice(0, 5);
    const reb_players_ids = all_player_ids.slice(5, 10);

    // Calculate average ELOs for the shuffled teams
    let imp_avg_elo = imp_players_ids.reduce((sum, id) => sum + p_ratings[id], 0) / imp_players_ids.length;
    let reb_avg_elo = reb_players_ids.reduce((sum, id) => sum + p_ratings[id], 0) / reb_players_ids.length;

    // Calculate expected outcomes
    let imp_expected = 1.0 / (1.0 + 10 ** ((reb_avg_elo - imp_avg_elo) / 400));
    let reb_expected = 1.0 - imp_expected;

    // Determine winner (Imp wins first 7, Reb wins last 3)
    let winner, imp_actual, reb_actual;
    if (i <= 7) {
        winner = "IMPERIAL"; imp_actual = 1.0; reb_actual = 0.0;
    } else {
        winner = "REBEL"; imp_actual = 0.0; reb_actual = 1.0;
    }

    // Calculate and record history/stats
    let imp_history = [];
    let reb_history = [];

    imp_players_ids.forEach(id => {
        let old_r = p_ratings[id];
        let new_r = old_r + k_factor * (imp_actual - imp_expected);
        imp_history.push({ player_id: id, player_name: `Player ${id}`, old_rating: old_r, new_rating: new_r, rating_change: new_r - old_r });
        p_ratings[id] = new_r; // Update rating for next calculation within this loop
        p_stats[id].played++;
        if (winner === 'IMPERIAL') p_stats[id].won++; else p_stats[id].lost++;
    });

    reb_players_ids.forEach(id => {
        let old_r = p_ratings[id];
        let new_r = old_r + k_factor * (reb_actual - reb_expected);
        reb_history.push({ player_id: id, player_name: `Player ${id}`, old_rating: old_r, new_rating: new_r, rating_change: new_r - old_r });
        p_ratings[id] = new_r; // Update rating for next calculation within this loop
        p_stats[id].played++;
        if (winner === 'REBEL') p_stats[id].won++; else p_stats[id].lost++;
    });

    // Add match to history
    dummyPickupEloHistory.push({
        match_id: match_id, match_date: match_date, season: "DUMMY_PICKUP",
        imperial_players: imp_history, rebel_players: reb_history, winner: winner
    });
}

// Generate final pickup ladder
dummyPickupEloLadder = Object.keys(p_ratings).map(id_str => {
    const id = parseInt(id_str);
    const stats = p_stats[id];
    const win_rate = stats.played > 0 ? Math.round((stats.won / stats.played) * 1000) / 10 : 0;
    return {
        player_id: id, player_name: `Player ${id}`, elo_rating: Math.round(p_ratings[id]),
        matches_played: stats.played, matches_won: stats.won, matches_lost: stats.lost, win_rate: win_rate
    };
});
dummyPickupEloLadder.sort((a, b) => b.elo_rating - a.elo_rating);
dummyPickupEloLadder.forEach((p, index) => p.rank = index + 1);

// --- End Dummy Data Generation ---


// Data storage (will be overwritten by dummy data)
let teamEloHistory = [];
let teamEloLadder = [];
let pickupEloHistory = [];
let pickupEloLadder = [];
let playerStats = []; // For additional leaderboards

// Chart instances for global access
let teamEloChartInstance = null;
let pickupEloChartInstance = null;

// DOM Elements
const teamEloChartCtx = document.getElementById('teamEloChart')?.getContext('2d');
const pickupEloChartCtx = document.getElementById('pickupEloChart')?.getContext('2d');
const teamEloTableBody = document.getElementById('teamEloTable')?.querySelector('tbody');
const pickupEloTableBody = document.getElementById('pickupEloTable')?.querySelector('tbody');

// --- Rendering Functions ---
function renderTeamEloChart() {
    console.log("Rendering Team ELO Chart...");
    if (!teamEloChartCtx || !teamEloHistory || teamEloHistory.length === 0) {
        console.warn("Team ELO Chart context or data not available.");
        const chartContainer = document.getElementById('teamEloChart')?.parentElement;
        if (chartContainer && !chartContainer.querySelector('.no-data-message')) {
            const msg = document.createElement('p');
            msg.textContent = 'Team ELO history data not available or chart canvas not found.';
            msg.className = 'no-data-message';
            chartContainer.appendChild(msg);
        }
        return;
    }

    // Process data for Chart.js
    const teamsData = {}; // { team_id: { name: 'Team Name', data: [{x: matchIndex, y: rating}] } }

    // 1. Add timestamp to each match object for sorting
    teamEloHistory.forEach(match => {
        try {
            // Robust manual parsing for "YYYY-MM-DD HH:MM:SS"
            const parts = match.match_date.match(/(\d{4})-(\d{2})-(\d{2}) (\d{2}):(\d{2}):(\d{2})/);
            if (parts) {
                const year = parseInt(parts[1], 10);
                const month = parseInt(parts[2], 10) - 1; // Month is 0-indexed in Date
                const day = parseInt(parts[3], 10);
                const hour = parseInt(parts[4], 10);
                const minute = parseInt(parts[5], 10);
                const second = parseInt(parts[6], 10);
                // Construct date explicitly
                const dateObj = new Date(Date.UTC(year, month, day, hour, minute, second)); // Use UTC to avoid timezone issues during parsing
                match.timestamp = dateObj.getTime();
            } else {
                 console.warn(`Could not parse date format: ${match.match_date} for match ID ${match.match_id}`);
                 match.timestamp = null; // Mark as invalid if format doesn't match
            }

            if (isNaN(match.timestamp)) {
                 console.warn(`Resulting timestamp is NaN for date: ${match.match_date} (match ID ${match.match_id})`);
                 match.timestamp = null; // Ensure NaN timestamps are treated as null
            }
        } catch (e) {
            console.error(`Error during manual date parsing for match ID ${match.match_id}: ${e.message}`);
            match.timestamp = null;
        }
    });

    // 2. Filter out matches with invalid dates and sort the history by timestamp
    const sortedHistory = teamEloHistory
        .filter(match => match.timestamp !== null)
        .sort((a, b) => a.timestamp - b.timestamp);

    // 3. Process sorted history to assign sequential index
    let matchIndex = 0;
    sortedHistory.forEach(match => {
        matchIndex++; // Increment for each valid, sorted match

        // Process Imperial team
        if (!teamsData[match.imperial.team_id]) {
            teamsData[match.imperial.team_id] = { name: match.imperial.team_name, data: [] };
        }
        teamsData[match.imperial.team_id].data.push({ x: matchIndex, y: match.imperial.old_rating });
        teamsData[match.imperial.team_id].data.push({ x: matchIndex, y: match.imperial.new_rating });

        // Process Rebel team
        if (!teamsData[match.rebel.team_id]) {
            teamsData[match.rebel.team_id] = { name: match.rebel.team_name, data: [] };
        }
        teamsData[match.rebel.team_id].data.push({ x: matchIndex, y: match.rebel.old_rating });
        teamsData[match.rebel.team_id].data.push({ x: matchIndex, y: match.rebel.new_rating });
    });

    // 4. Sort data points within each team's dataset by index (ensures correct line drawing)
    for (const teamId in teamsData) {
        teamsData[teamId].data.sort((a, b) => a.x - b.x);
    }

    const datasets = Object.values(teamsData).map(team => ({
        label: team.name,
        data: team.data,
        fill: false,
        borderColor: getRandomColor(), // Function to generate random colors
        tension: 0.1,
        pointRadius: 2, // Smaller points
        pointHoverRadius: 5
    }));

    // Destroy previous chart instance if it exists
    if (teamEloChartInstance) {
        teamEloChartInstance.destroy();
    }

    // Create the chart
    teamEloChartInstance = new Chart(teamEloChartCtx, {
        type: 'line',
        data: {
            datasets: datasets
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                x: {
                    type: 'linear', // Use linear scale for match sequence
                    title: {
                        display: true,
                        text: 'Match Sequence' // Update axis title
                    },
                    ticks: {
                        stepSize: 1, // Try to show integer ticks
                        precision: 0 // Ensure no decimal places on ticks
                    }
                },
                y: {
                    title: {
                        display: true,
                        text: 'ELO Rating'
                    },
                    beginAtZero: false // ELO doesn't start at 0
                }
            },
            plugins: {
                tooltip: {
                    mode: 'index',
                    intersect: false,
                },
                legend: {
                    position: 'top', // Or 'bottom', 'left', 'right'
                    labels: {
                        boxWidth: 12,
                        padding: 15
                    }
                }
            },
            interaction: { // For better hover behavior
                mode: 'nearest',
                axis: 'x',
                intersect: false
            }
        }
    });
    
    // Apply enhanced chart interactivity (Phase 2 feature)
    enhanceChartInteractivity(teamEloChartInstance);
    addChartControls('teamEloChart');
    
    console.log("Team ELO Chart rendered.");
}

// Helper function to generate random colors for chart lines
function getRandomColor() {
    const letters = '0123456789ABCDEF';
    let color = '#';
    for (let i = 0; i < 6; i++) {
        color += letters[Math.floor(Math.random() * 16)];
    }
    return color;
}

function renderPickupEloChart() {
    console.log("Rendering Pickup Player ELO Chart...");
    if (!pickupEloChartCtx || !pickupEloHistory || pickupEloHistory.length === 0) {
        console.warn("Pickup ELO Chart context or data not available.");
        const chartContainer = document.getElementById('pickupEloChart')?.parentElement;
        if (chartContainer && !chartContainer.querySelector('.no-data-message')) {
            const msg = document.createElement('p');
            msg.textContent = 'Pickup Player ELO history data not available or chart canvas not found.';
            msg.className = 'no-data-message';
            chartContainer.appendChild(msg);
        }
        return;
    }

    // Process data for Chart.js
    const playersData = {}; // { player_id: { name: 'Player Name', data: [{x: matchIndex, y: rating}] } }
    const playersInHistory = new Set(); // Keep track of players who actually have history entries

    // 1. Add timestamp to each match object for sorting
    pickupEloHistory.forEach(match => {
        try {
            // Robust manual parsing for "YYYY-MM-DD HH:MM:SS"
            const parts = match.match_date.match(/(\d{4})-(\d{2})-(\d{2}) (\d{2}):(\d{2}):(\d{2})/);
            if (parts) {
                const year = parseInt(parts[1], 10);
                const month = parseInt(parts[2], 10) - 1; // Month is 0-indexed in Date
                const day = parseInt(parts[3], 10);
                const hour = parseInt(parts[4], 10);
                const minute = parseInt(parts[5], 10);
                const second = parseInt(parts[6], 10);
                // Construct date explicitly
                const dateObj = new Date(Date.UTC(year, month, day, hour, minute, second)); // Use UTC to avoid timezone issues during parsing
                match.timestamp = dateObj.getTime();
            } else {
                 console.warn(`Could not parse date format: ${match.match_date} for pickup match ID ${match.match_id}`);
                 match.timestamp = null; // Mark as invalid if format doesn't match
            }

            if (isNaN(match.timestamp)) {
                 console.warn(`Resulting timestamp is NaN for date: ${match.match_date} (pickup match ID ${match.match_id})`);
                 match.timestamp = null; // Ensure NaN timestamps are treated as null
            }
        } catch (e) {
            console.error(`Error during manual date parsing for pickup match ID ${match.match_id}: ${e.message}`);
            match.timestamp = null;
        }
    });

    // 2. Filter out matches with invalid dates and sort the history by timestamp
    const sortedHistory = pickupEloHistory
        .filter(match => match.timestamp !== null)
        .sort((a, b) => a.timestamp - b.timestamp);

    // 3. Process sorted history to assign sequential index
    let matchIndex = 0;
    sortedHistory.forEach(match => {
        matchIndex++; // Increment for each valid, sorted match

        // Combine imperial and rebel players for processing
        const allPlayersInMatch = [...match.imperial_players, ...match.rebel_players];

        allPlayersInMatch.forEach(player => {
            playersInHistory.add(player.player_id); // Mark player as having history data
            if (!playersData[player.player_id]) {
                playersData[player.player_id] = { name: player.player_name, data: [] };
            }
            // Add ratings using the matchIndex
            playersData[player.player_id].data.push({ x: matchIndex, y: player.old_rating });
            playersData[player.player_id].data.push({ x: matchIndex, y: player.new_rating });
        });
    });

    // 4. Sort data points within each player's dataset by index
    for (const playerId in playersData) {
        playersData[playerId].data.sort((a, b) => a.x - b.x);
    }

    // --- Filtering Logic (Optional - Show only Top N players by final ELO) ---
    // To avoid cluttering the chart, let's show only the top N players based on their final rating in the ladder data
    const topN = 15; // Show top 15 players, adjust as needed
    const sortedLadder = pickupEloLadder.sort((a, b) => b.elo_rating - a.elo_rating);
    const topPlayerIds = new Set(sortedLadder.slice(0, topN).map(p => p.player_id));

    const datasets = Object.entries(playersData)
        .filter(([playerId, playerData]) => topPlayerIds.has(parseInt(playerId))) // Filter for top N players
        .map(([playerId, playerData]) => ({
            label: playerData.name,
            data: playerData.data,
            fill: false,
            borderColor: getRandomColor(),
            tension: 0.1,
            pointRadius: 2,
            pointHoverRadius: 5
        }));

    // Destroy previous chart instance if it exists
    if (pickupEloChartInstance) {
        pickupEloChartInstance.destroy();
    }

    // Create the chart
    pickupEloChartInstance = new Chart(pickupEloChartCtx, {
        type: 'line',
        data: {
            datasets: datasets
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                x: {
                    type: 'linear', // Use linear scale for match sequence
                    title: {
                        display: true,
                        text: 'Match Sequence' // Update axis title
                    },
                    ticks: {
                        stepSize: 1, // Try to show integer ticks
                        precision: 0 // Ensure no decimal places on ticks
                    }
                },
                y: {
                    title: {
                        display: true,
                        text: 'ELO Rating'
                    },
                    beginAtZero: false
                }
            },
            plugins: {
                tooltip: {
                    mode: 'index',
                    intersect: false,
                },
                legend: {
                    position: 'top',
                    labels: {
                        boxWidth: 12,
                        padding: 15
                    }
                }
            },
            interaction: {
                mode: 'nearest',
                axis: 'x',
                intersect: false
            }
        }
    });
    
    // Apply enhanced chart interactivity (Phase 2 feature)
    enhanceChartInteractivity(pickupEloChartInstance);
    addChartControls('pickupEloChart');
    
    console.log("Pickup Player ELO Chart rendered.");
}

// Function to render team table is not used in combined view

// Function to render pickup table is not used in combined view

// Function to apply interactive features to tables is not used in combined view

// Function to create additional leaderboards is not used in combined view

async function renderVisualizations() {
    try {
        console.log("Starting visualization rendering...");

        // Call only chart rendering functions for combined view
        renderTeamEloChart();
        renderPickupEloChart();
        
        // Table rendering and additional leaderboards removed from combined view
        
        console.log("All visualizations rendered successfully");
    } catch (error) {
        console.error("Error rendering visualizations:", error);
        document.body.innerHTML += `<div style="color: red; padding: 20px; margin: 20px; border: 1px solid red; background: #ffeeee;">
            <h2>Error Rendering Visualizations</h2>
            <p>There was an error rendering the visualizations. Please check the console for details.</p>
            <p>Error: ${error.message}</p>
        </div>`;
    }
}

// --- Initialization ---
// Load real data instead of using dummy data
async function initializeData() {
    try {
        console.log("Initializing data...");
        
        // Check if we should use real data or dummy data
        // You can change this based on a URL parameter, local storage setting, etc.
        const useRealData = true;
        
        if (useRealData) {
            console.log("Loading real data...");
            
            try {
                // Import the real data loader dynamically
                const realDataModule = await import('./js/realdata_fixed.js');
                const { loadAllRealData } = realDataModule;
                
                // Load all real data
                const data = await loadAllRealData();
                
                // Debug log to show what data was loaded
                console.log("Real data contents:");
                console.log("Pickup ladder length:", data.pickupEloLadder?.length || 0);
                console.log("First pickup player:", data.pickupEloLadder?.[0] || "None");
                console.log("Roles data:", Object.keys(data.playerRoles || {}).length);
                
                // Make data available globally
                window.teamEloHistory = teamEloHistory = data.teamEloHistory;
                window.teamEloLadder = teamEloLadder = data.teamEloLadder;
                window.pickupEloHistory = pickupEloHistory = data.pickupEloHistory;
                window.pickupEloLadder = pickupEloLadder = data.pickupEloLadder;
                window.playerStats = playerStats = data.playerStats;
                window.playerRoles = data.playerRoles; // Add player roles for global access
                
                console.log("Real data loaded successfully");
            } catch (error) {
                console.error("Error loading real data:", error);
                console.log("Falling back to dummy data...");
                
                // Fall back to dummy data if real data loading fails
                window.teamEloHistory = teamEloHistory = dummyTeamEloHistory;
                window.teamEloLadder = teamEloLadder = dummyTeamEloLadder;
                window.pickupEloHistory = pickupEloHistory = dummyPickupEloHistory;
                window.pickupEloLadder = pickupEloLadder = dummyPickupEloLadder;
                
                // Generate player stats for additional leaderboards
                playerStats = generateDummyPlayerStats();
            }
        } else {
            console.log("Using dummy data...");
            
            // Use dummy data
            window.teamEloHistory = teamEloHistory = dummyTeamEloHistory;
            window.teamEloLadder = teamEloLadder = dummyTeamEloLadder;
            window.pickupEloHistory = pickupEloHistory = dummyPickupEloHistory;
            window.pickupEloLadder = pickupEloLadder = dummyPickupEloLadder;
            
            // Generate player stats for additional leaderboards
            playerStats = generateDummyPlayerStats();
        }

        // Render visualizations with the data
        await renderVisualizations();
        
        console.log("Initialization complete");
    } catch (error) {
        console.error("Error initializing data:", error);
    }
}

// Start initialization
initializeData();
}