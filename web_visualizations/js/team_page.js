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
            const { makeTableSortable, addTableFilter, enableTableRowSelection, addRoleFilter, filterTableByRole } = tableInteractivity;
            console.log('tableInteractivity.js loaded successfully');

            console.log('Loading chartInteractivity.js...');
            const chartInteractivity = await import('./chartInteractivity.js');
            const { enhanceChartInteractivity, filterChartByName, addChartControls } = chartInteractivity;
            console.log('chartInteractivity.js loaded successfully');

            console.log('Loading leaderboardManager.js...');
            const leaderboardManager = await import('./leaderboardManager.js');
            const { createAdditionalLeaderboards, filterAllLeaderboards } = leaderboardManager;
            console.log('leaderboardManager.js loaded successfully');

            console.log('Loading realdata_fixed.js...');
            const realData = await import('./realdata_fixed.js');
            const { loadAllRealData } = realData;
            console.log('realdata_fixed.js loaded successfully');

            const moduleEnd = performance.now();
            console.log(`All modules loaded in ${(moduleEnd - moduleStart).toFixed(2)}ms`);

            // Now that modules are loaded, initialize the app
            // Pass all necessary functions, including the newly imported one
            initializeApp({
                makeTableSortable,
                addTableFilter,
                enableTableRowSelection,
                enhanceChartInteractivity,
                filterChartByName,
                addChartControls,
                createAdditionalLeaderboards,
                filterAllLeaderboards, // Pass the function here
                loadAllRealData,
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
        loadAllRealData,
        addRoleFilter,
        filterTableByRole,
        filterAllLeaderboards // Destructure the function here
    } = modules;

    // Data storage
    let teamEloHistory = [];
    let teamEloLadder = [];
    let playerStats = []; // For additional leaderboards
    let playerRoles = {}; // For role filtering

    // Chart instances
    let teamEloChartInstance = null;

    // DOM Elements
    const teamEloChartCtx = document.getElementById('teamEloChart')?.getContext('2d');
    const teamEloTableBody = document.getElementById('teamEloTable')?.querySelector('tbody');

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
        const teamsData = {}; // { team_id: { name: 'Team Name', data: [{x: index, y: rating}] } }

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
    
    // Fixed function for team_page.js to properly display win rate

    function renderTeamEloTable() {
        console.log("Rendering Team ELO Table...");
        if (!teamEloTableBody || !teamEloLadder || teamEloLadder.length === 0) {
            console.warn("Team ELO table body or data not available.");
            const table = document.getElementById('teamEloTable');
            if (table && !table.querySelector('.no-data-message')) {
                const msgRow = table.insertRow();
                const cell = msgRow.insertCell();
                cell.colSpan = 5; // Span across all columns (updated from 6 to 5 since we removed a column)
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
            // Use the win_rate directly from the data
            winRateCell.textContent = `${team.win_rate}%`;
        });
        console.log("Team ELO Table populated.");
    }

    // Function to apply interactive features to tables
    function applyTableInteractivity() {
        console.log("Applying table interactivity features...");
        
        // Make team ELO table sortable
        makeTableSortable('teamEloTable');
        // Removed addTableFilter call since we removed the search field
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
            
            // Create leaderboards
            const leaderboardSection = await createAdditionalLeaderboards('#leaderboards-container', playerStats);
            
            // Only add role filters if we have player stats
            if (playerStats && playerStats.length > 0) {
                // Extract unique roles from player stats
                const uniqueRoles = new Set();
                
                // Debug: Check each player's role
                console.log("Checking roles for each player:");
                playerStats.forEach(player => {
                    console.log(`  Player ${player.player_name}: role = "${player.role || 'null/undefined'}"`);
                    if (player.role) {
                        uniqueRoles.add(player.role);
                    }
                });
                
                console.log(`Found ${uniqueRoles.size} unique roles: ${Array.from(uniqueRoles).join(', ')}`);
                
                // Only add role filter if we have role data
                if (uniqueRoles.size > 0) {
                    console.log("Adding role filter buttons");
                    addRoleFilter('aiKillsTable', Array.from(uniqueRoles));
                    console.log(`Added role filter with ${uniqueRoles.size} roles: ${Array.from(uniqueRoles).join(', ')}`);

                    // Connect role filter button clicks to filter all leaderboards
                    document.addEventListener('roleFilterChanged', (e) => {
                        const selectedRole = e.detail.role;
                        console.log(`Filtering leaderboards and chart for role: ${selectedRole}`);
                        filterAllLeaderboards(selectedRole);
                    });
                } else {
                    console.log("No roles found, not adding role filter");
                    
                    // Even if we don't have roles in the data, let's add some default role buttons for testing
                    console.log("Adding default role buttons");
                    addRoleFilter('aiKillsTable', ['Farmer', 'Flex', 'Support']);
                }
                
                // Add separate listener to filter leaderboards when role buttons are clicked
                const roleFilterContainer = document.getElementById('roleFilterContainer');
                if (roleFilterContainer) {
                    // Use a flag to prevent adding the listener multiple times if this function is called again
                    if (!roleFilterContainer.dataset.leaderboardListenerAdded) {
                        roleFilterContainer.addEventListener('click', (e) => {
                            const target = e.target;
                            // Ensure it's a role button click
                            if (target.classList.contains('role-filter-button') && target.dataset.role) {
                                const selectedRole = target.dataset.role;
                                console.log(`Filtering leaderboards for role: ${selectedRole}`);
                                
                                // Filter the leaderboards
                                filterAllLeaderboards(selectedRole);
                            }
                        });
                        roleFilterContainer.dataset.leaderboardListenerAdded = 'true'; // Mark listener as added
                        console.log("Added separate event listener for role filtering.");
                    }
                }
            }
            
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
            
            // Set global flag to indicate team page
            window.isTeamPage = true;
            document.title = "Team Stats - Squadrons Visualizations"; // Force title to include team
            
            // Load real data
            const data = await loadAllRealData();
            
            // Validate that we have team data
            if (!data.teamEloLadder || data.teamEloLadder.length === 0) {
                console.error("No team ladder data loaded!");
                document.body.innerHTML += `
                    <div style="color: red; padding: 20px; margin: 20px; border: 1px solid red; background: #ffeeee;">
                        <h2>Team Data Not Found</h2>
                        <p>Could not load team ELO ladder data. Please ensure that team data has been generated.</p>
                        <p>Expected file: ../stats_reports/elo_ladder_team.json</p>
                    </div>
                `;
            }
            
            // Store data for use in rendering
            teamEloHistory = data.teamEloHistory;
            teamEloLadder = data.teamEloLadder;
            playerRoles = data.playerRoles;
            
            // Use player stats for role information
            playerStats = data.playerStats;
            
            console.log("Team data loaded successfully");
            console.log("Team ladder entries:", teamEloLadder.length);
            console.log("Team history entries:", teamEloHistory.length);
            console.log("Player stats entries:", playerStats.length);
            
            // Render visualizations
            await renderVisualizations();
            
            // Add event listeners to the hardcoded role filter buttons
            const roleFilterButtons = document.querySelectorAll('.role-filter-button');
            roleFilterButtons.forEach(button => {
                button.addEventListener('click', () => {
                    const role = button.dataset.role;
                    console.log(`Role button clicked: ${role}`);
                    
                    // Remove active class from all buttons
                    document.querySelectorAll('.role-filter-button').forEach(btn => {
                        btn.classList.remove('active');
                        btn.style.backgroundColor = '#333333';
                        btn.style.color = '#e0e0e0';
                    });
                    
                    // Add active class to clicked button
                    button.classList.add('active');
                    button.style.backgroundColor = '#0066cc';
                    button.style.color = 'white';
                    
                    // Filter leaderboards
                    filterAllLeaderboards(role);
                });
            });
            
            console.log("Team page initialization complete");
        } catch (error) {
            console.error("Error initializing team data:", error);
            document.body.innerHTML += `
                <div style="color: red; padding: 20px; margin: 20px; border: 1px solid red; background: #ffeeee;">
                    <h2>Error Loading Team Data</h2>
                    <p>There was an error initializing the team data: ${error.message}</p>
                </div>
            `;
        }
    }

    // Start initialization
    initializeData();
}