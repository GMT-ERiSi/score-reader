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

// DOM Elements
const teamEloChartCtx = document.getElementById('teamEloChart')?.getContext('2d');
const pickupEloChartCtx = document.getElementById('pickupEloChart')?.getContext('2d');
const teamEloTableBody = document.getElementById('teamEloTable')?.querySelector('tbody');
const pickupEloTableBody = document.getElementById('pickupEloTable')?.querySelector('tbody');

// --- Data Fetching (Commented out to use dummy data) ---
/*
async function fetchData() {
    // ... (original fetch code remains here but is inactive)
}
*/

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
    const teamsData = {}; // { team_id: { name: 'Team Name', data: [{x: date, y: rating}] } }
    const allDates = new Set();

    teamEloHistory.forEach(match => {
        // Parse date string reliably and get timestamp for Chart.js
        const matchTimestamp = new Date(match.match_date.replace(' ', 'T')).getTime();
        if (isNaN(matchTimestamp)) { // Check if parsing failed
             console.warn(`Invalid date format found in team history: ${match.match_date} for match ID ${match.match_id}`);
             return; // Skip this match entry if date is invalid
        }
        allDates.add(matchTimestamp); // Use the timestamp

        // Process Imperial team
        if (!teamsData[match.imperial.team_id]) {
            teamsData[match.imperial.team_id] = { name: match.imperial.team_name, data: [] };
        }
        // Add rating *before* the match using timestamp
        teamsData[match.imperial.team_id].data.push({ x: matchTimestamp, y: match.imperial.old_rating });
        // Add rating *after* the match using timestamp
        teamsData[match.imperial.team_id].data.push({ x: matchTimestamp, y: match.imperial.new_rating });


        // Process Rebel team
        if (!teamsData[match.rebel.team_id]) {
            teamsData[match.rebel.team_id] = { name: match.rebel.team_name, data: [] };
        }
         // Add rating *before* the match using timestamp
        teamsData[match.rebel.team_id].data.push({ x: matchTimestamp, y: match.rebel.old_rating });
         // Add rating *after* the match using timestamp
        teamsData[match.rebel.team_id].data.push({ x: matchTimestamp, y: match.rebel.new_rating });
    });

     // Sort data points by date for each team
    for (const teamId in teamsData) {
        teamsData[teamId].data.sort((a, b) => new Date(a.x) - new Date(b.x));
         // Optional: Remove duplicate consecutive points if rating didn't change between matches
         // This can simplify the chart visually but requires more complex logic
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
    if (window.teamEloChartInstance) {
        window.teamEloChartInstance.destroy();
    }

    // Create the chart
    window.teamEloChartInstance = new Chart(teamEloChartCtx, {
        type: 'line',
        data: {
            datasets: datasets
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                x: {
                    type: 'time',
                    time: {
                        unit: 'day', // Adjust time unit as needed (day, week, month)
                         tooltipFormat: 'PPP p', // Format for tooltips e.g., Aug 15, 2024, 12:00:00 PM
                         displayFormats: {
                             day: 'MMM d, yyyy' // Format for axis labels
                         }
                    },
                    title: {
                        display: true,
                        text: 'Match Date'
                    },
                     ticks: {
                         autoSkip: true,
                         maxTicksLimit: 15 // Limit number of ticks on x-axis
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
    const playersData = {}; // { player_id: { name: 'Player Name', data: [{x: date, y: rating}] } }
    const allDates = new Set();
    const playersInHistory = new Set(); // Keep track of players who actually have history entries

    pickupEloHistory.forEach(match => {
        // Parse date string reliably and get timestamp for Chart.js
        const matchTimestamp = new Date(match.match_date.replace(' ', 'T')).getTime();
         if (isNaN(matchTimestamp)) { // Check if parsing failed
             console.warn(`Invalid date format found in pickup history: ${match.match_date} for match ID ${match.match_id}`);
             return; // Skip this match entry if date is invalid
         }
        allDates.add(matchTimestamp); // Use the timestamp

        // Combine imperial and rebel players for processing
        const allPlayersInMatch = [...match.imperial_players, ...match.rebel_players];

        allPlayersInMatch.forEach(player => {
            playersInHistory.add(player.player_id); // Mark player as having history data
            if (!playersData[player.player_id]) {
                playersData[player.player_id] = { name: player.player_name, data: [] };
            }
             // Add rating *before* the match using timestamp
            playersData[player.player_id].data.push({ x: matchTimestamp, y: player.old_rating });
             // Add rating *after* the match using timestamp
            playersData[player.player_id].data.push({ x: matchTimestamp, y: player.new_rating });
        });
    });

     // Sort data points by date for each player
    for (const playerId in playersData) {
        playersData[playerId].data.sort((a, b) => new Date(a.x) - new Date(b.x));
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
    if (window.pickupEloChartInstance) {
        window.pickupEloChartInstance.destroy();
    }

    // Create the chart
    window.pickupEloChartInstance = new Chart(pickupEloChartCtx, {
        type: 'line',
        data: {
            datasets: datasets
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                x: {
                    type: 'time',
                    time: {
                        unit: 'day',
                        tooltipFormat: 'PPP p',
                         displayFormats: {
                             day: 'MMM d, yyyy'
                         }
                    },
                    title: {
                        display: true,
                        text: 'Match Date'
                    },
                     ticks: {
                         autoSkip: true,
                         maxTicksLimit: 15
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
                         padding: 15,
                         // Optional: Filter legend items if too many
                         // filter: function(legendItem, chartData) {
                         //     // Logic to decide if legendItem should be shown
                         //     return true;
                         // }
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
     console.log("Pickup Player ELO Chart rendered.");
}

function renderTeamEloTable() {
    console.log("Rendering Team ELO Table...");
    if (!teamEloTableBody || !teamEloLadder || teamEloLadder.length === 0) {
         console.warn("Team ELO table body or data not available.");
         const table = document.getElementById('teamEloTable');
         if (table && !table.querySelector('.no-data-message')) {
             const msgRow = table.insertRow();
             const cell = msgRow.insertCell();
             cell.colSpan = 5; // Span across all columns
             cell.textContent = 'Team ELO ladder data not available.';
             cell.className = 'no-data-message';
             cell.style.textAlign = 'center';
         }
        return;
    }
    // Clear previous data
    teamEloTableBody.innerHTML = '';

    // Ensure ladder is sorted by rank (it should be already, but just in case)
    const sortedLadder = teamEloLadder.sort((a, b) => a.rank - b.rank);

    // Populate table rows
    sortedLadder.forEach(team => {
        const row = teamEloTableBody.insertRow();

        const rankCell = row.insertCell();
        rankCell.textContent = team.rank;

        const nameCell = row.insertCell();
        nameCell.textContent = team.team_name;

        const eloCell = row.insertCell();
        eloCell.textContent = team.elo_rating;

        const wlCell = row.insertCell();
        wlCell.textContent = `${team.matches_won}-${team.matches_lost}`;

        const winRateCell = row.insertCell();
        winRateCell.textContent = `${team.win_rate}%`;
    });
    console.log("Team ELO Table populated.");
}

function renderPickupEloTable() {
    console.log("Rendering Pickup Player ELO Table...");
     if (!pickupEloTableBody || !pickupEloLadder || pickupEloLadder.length === 0) {
         console.warn("Pickup ELO table body or data not available.");
         const table = document.getElementById('pickupEloTable');
         if (table && !table.querySelector('.no-data-message')) {
             const msgRow = table.insertRow();
             const cell = msgRow.insertCell();
             cell.colSpan = 5; // Span across all columns
             cell.textContent = 'Pickup Player ELO ladder data not available.';
             cell.className = 'no-data-message';
             cell.style.textAlign = 'center';
         }
        return;
    }
     // Clear previous data
    pickupEloTableBody.innerHTML = '';

    // Ensure ladder is sorted by rank
    const sortedLadder = pickupEloLadder.sort((a, b) => a.rank - b.rank);

    // Populate table rows
    sortedLadder.forEach(player => {
        const row = pickupEloTableBody.insertRow();

        const rankCell = row.insertCell();
        rankCell.textContent = player.rank;

        const nameCell = row.insertCell();
        nameCell.textContent = player.player_name; // Use player_name

        const eloCell = row.insertCell();
        eloCell.textContent = player.elo_rating;

        const wlCell = row.insertCell();
        wlCell.textContent = `${player.matches_won}-${player.matches_lost}`;

        const winRateCell = row.insertCell();
        winRateCell.textContent = `${player.win_rate}%`;
    });
     console.log("Pickup Player ELO Table populated.");
}

function renderVisualizations() {
    // Call individual rendering functions
    renderTeamEloChart();
    renderPickupEloChart();
    renderTeamEloTable();
    renderPickupEloTable();
}

// --- Initialization ---
// Use dummy data instead of fetching
document.addEventListener('DOMContentLoaded', () => {
    console.log("Using dummy data for visualization.");
    // Assign dummy data to global variables
    teamEloHistory = dummyTeamEloHistory;
    teamEloLadder = dummyTeamEloLadder;
    pickupEloHistory = dummyPickupEloHistory;
    pickupEloLadder = dummyPickupEloLadder;

    // Render visualizations with dummy data
    renderVisualizations();
});