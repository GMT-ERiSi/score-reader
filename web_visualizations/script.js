// Data storage
let teamEloHistory = [];
let teamEloLadder = [];
let pickupEloHistory = [];
let pickupEloLadder = [];

// DOM Elements (optional, can get them inside functions too)
const teamEloChartCtx = document.getElementById('teamEloChart')?.getContext('2d');
const pickupEloChartCtx = document.getElementById('pickupEloChart')?.getContext('2d');
const teamEloTableBody = document.getElementById('teamEloTable')?.querySelector('tbody');
const pickupEloTableBody = document.getElementById('pickupEloTable')?.querySelector('tbody');

// --- Data Fetching ---
async function fetchData() {
    console.log("Fetching data...");
    try {
        // Use Promise.all to fetch data concurrently
        const [
            teamHistoryRes,
            teamLadderRes,
            pickupHistoryRes,
            pickupLadderRes
        ] = await Promise.all([
            fetch('../stats_reports/elo_history_team.json'), // Relative path from index.html
            fetch('../stats_reports/elo_ladder_team.json'),
            fetch('../elo_reports_pickup/pickup_player_elo_history.json'),
            fetch('../elo_reports_pickup/pickup_player_elo_ladder.json')
        ]);

        // Check responses
        if (!teamHistoryRes.ok) throw new Error(`Failed to fetch team history: ${teamHistoryRes.statusText}`);
        if (!teamLadderRes.ok) throw new Error(`Failed to fetch team ladder: ${teamLadderRes.statusText}`);
        if (!pickupHistoryRes.ok) throw new Error(`Failed to fetch pickup history: ${pickupHistoryRes.statusText}`);
        if (!pickupLadderRes.ok) throw new Error(`Failed to fetch pickup ladder: ${pickupLadderRes.statusText}`);

        // Parse JSON data
        teamEloHistory = await teamHistoryRes.json();
        teamEloLadder = await teamLadderRes.json();
        pickupEloHistory = await pickupHistoryRes.json();
        pickupEloLadder = await pickupLadderRes.json();

        console.log("Data fetched successfully:", { teamEloHistory, teamEloLadder, pickupEloHistory, pickupEloLadder });

        // Once data is loaded, render the visualizations
        renderVisualizations();

    } catch (error) {
        console.error("Error fetching data:", error);
        // Display error message to the user (optional)
        const body = document.querySelector('body');
        if (body) {
            const errorDiv = document.createElement('div');
            errorDiv.textContent = `Error loading data: ${error.message}. Please ensure report files exist in the correct locations ('stats_reports/' and 'elo_reports_pickup/').`;
            errorDiv.style.color = 'red';
            errorDiv.style.padding = '10px';
            errorDiv.style.border = '1px solid red';
            errorDiv.style.marginTop = '20px';
            body.insertBefore(errorDiv, body.firstChild);
        }
    }
}

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
// Add event listener to run fetchData when the DOM is fully loaded
document.addEventListener('DOMContentLoaded', fetchData);