// team_page.js - Load and display team-specific data
console.log('Team page script loading...');

// Import our modular components
try {
    const moduleStart = performance.now();
    console.log('Importing modules...');

    // Dynamic imports
    async function loadModules() {
        try {
            console.log('Loading tableInteractivity.js...');
            const tableInteractivity = await import('./tableInteractivity.js');
            const { makeTableSortable, addTableFilter, enableTableRowSelection } = tableInteractivity;
            console.log('tableInteractivity.js loaded successfully');

            console.log('Loading chartInteractivity.js...');
            const chartInteractivity = await import('./chartInteractivity.js');
            const { enhanceChartInteractivity, filterChartByName, addChartControls } = chartInteractivity;
            console.log('chartInteractivity.js loaded successfully');

            console.log('Loading leaderboardManager.js...');
            const leaderboardManager = await import('./leaderboardManager.js');
            const { createAdditionalLeaderboards } = leaderboardManager;
            console.log('leaderboardManager.js loaded successfully');

            console.log('Loading realdata_fixed.js...');
            const realData = await import('./realdata_fixed.js');
            const { loadAllRealData } = realData;
            console.log('realdata_fixed.js loaded successfully');

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
                loadAllRealData
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
    console.error('Critical error in team_page.js:', error);
}

// Initialize application with imported modules
function initializeApp(modules) {
    console.log('Initializing team page application...');
    
    const {
        makeTableSortable, 
        addTableFilter, 
        enableTableRowSelection,
        enhanceChartInteractivity,
        filterChartByName,
        addChartControls,
        createAdditionalLeaderboards,
        loadAllRealData
    } = modules;

    // Data storage
    let teamEloHistory = [];
    let teamEloLadder = [];
    let playerStats = []; // For additional leaderboards

    // Chart instances
    let teamEloChartInstance = null;

    // DOM Elements
    const teamEloChartCtx = document.getElementById('teamEloChart')?.getContext('2d');
    const teamEloTableBody = document.getElementById('teamEloTable')?.querySelector('tbody');

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
            // Try to parse the date
            let matchTimestamp;
            try {
                matchTimestamp = new Date(match.match_date.replace(' ', 'T')).getTime();
                
                if (isNaN(matchTimestamp)) {
                    // Try alternative date formats if needed
                    const dateParts = match.match_date.split(/[\s-:]/);
                    if (dateParts.length >= 3) {
                        const correctedDate = `${dateParts[0]}-${dateParts[2]}-${dateParts[1]} ${dateParts[3] || '12'}:${dateParts[4] || '00'}:${dateParts[5] || '00'}`;
                        matchTimestamp = new Date(correctedDate.replace(' ', 'T')).getTime();
                    }
                }
            } catch (e) {
                console.warn(`Error parsing date: ${e.message}`);
                matchTimestamp = NaN;
            }
            
            if (isNaN(matchTimestamp)) {
                console.warn(`Invalid date format found in team history: ${match.match_date} for match ID ${match.match_id}`);
                return; // Skip this match entry if date is invalid
            }
            
            allDates.add(matchTimestamp); // Use the timestamp

            // Process Imperial team
            if (!teamsData[match.imperial.team_id]) {
                teamsData[match.imperial.team_id] = { name: match.imperial.team_name, data: [] };
            }
            // Add rating points
            teamsData[match.imperial.team_id].data.push({ x: matchTimestamp, y: match.imperial.old_rating });
            teamsData[match.imperial.team_id].data.push({ x: matchTimestamp, y: match.imperial.new_rating });

            // Process Rebel team
            if (!teamsData[match.rebel.team_id]) {
                teamsData[match.rebel.team_id] = { name: match.rebel.team_name, data: [] };
            }
            // Add rating points
            teamsData[match.rebel.team_id].data.push({ x: matchTimestamp, y: match.rebel.old_rating });
            teamsData[match.rebel.team_id].data.push({ x: matchTimestamp, y: match.rebel.new_rating });
        });

        // Sort data points by date for each team
        for (const teamId in teamsData) {
            teamsData[teamId].data.sort((a, b) => a.x - b.x);
        }

        // Generate datasets for Chart.js
        const datasets = Object.values(teamsData).map(team => ({
            label: team.name,
            data: team.data,
            fill: false,
            borderColor: getRandomColor(), // Function to generate random colors
            tension: 0.1,
            pointRadius: 2,
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
                        beginAtZero: false // ELO doesn't start at 0
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
        
        // Apply enhanced chart interactivity
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
            rankCell.classList.add('rank-cell');

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

    // Function to apply interactive features to tables
    function applyTableInteractivity() {
        console.log("Applying table interactivity features...");
        
        // Make team ELO table sortable
        makeTableSortable('teamEloTable');
        addTableFilter('teamEloTable', 'Search teams...');
        enableTableRowSelection('teamEloTable', (teamName) => {
            filterChartByName(teamEloChartInstance, teamName);
        });
        
        // Add button event listener for showing all teams
        const showAllButton = document.getElementById('showAllTeamsButton');
        if (showAllButton) {
            showAllButton.addEventListener('click', () => {
                filterChartByName(teamEloChartInstance, null); // Clear filters
                
                // Clear any selected rows
                const selectedRows = document.querySelectorAll('#teamEloTable tbody tr.selected');
                selectedRows.forEach(row => row.classList.remove('selected'));
            });
        }
        
        console.log("Table interactivity features applied.");
    }

    async function renderVisualizations() {
        try {
            console.log("Starting team visualization rendering...");

            // Call individual rendering functions
            renderTeamEloChart();
            renderTeamEloTable();
            
            // Apply interactivity
            applyTableInteractivity();
            await createAdditionalLeaderboards('#leaderboards-container', playerStats);
            
            console.log("All team visualizations rendered successfully");
        } catch (error) {
            console.error("Error rendering team visualizations:", error);
            document.body.innerHTML += `<div style="color: red; padding: 20px; margin: 20px; border: 1px solid red; background: #ffeeee;">
                <h2>Error Rendering Visualizations</h2>
                <p>There was an error rendering the visualizations. Please check the console for details.</p>
                <p>Error: ${error.message}</p>
            </div>`;
        }
    }

    // Initialize data and render
    async function initializeData() {
        try {
            console.log("Initializing team data...");
            
            // Load real data
            const data = await loadAllRealData();
            
            // Store data for use in rendering
            teamEloHistory = data.teamEloHistory;
            teamEloLadder = data.teamEloLadder;
            playerStats = data.playerStats;
            
            console.log("Team data loaded successfully");
            console.log("Team ladder entries:", teamEloLadder.length);
            console.log("Team history entries:", teamEloHistory.length);
            
            // Render visualizations
            await renderVisualizations();
            
            console.log("Team page initialization complete");
        } catch (error) {
            console.error("Error initializing team data:", error);
        }
    }

    // Start initialization
    initializeData();
}