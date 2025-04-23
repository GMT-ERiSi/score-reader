// pickup_page.js - Load and display pickup-specific data
console.log('Pickup page script loading...');

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
            const { createAdditionalLeaderboards, filterAllLeaderboards } = leaderboardManager; // Import filter function
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
    console.error('Critical error in pickup_page.js:', error);
}

// Initialize application with imported modules
function initializeApp(modules) {
    console.log('Initializing pickup page application...');
    
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
    let pickupEloHistory = [];
    let pickupEloLadder = [];
    let playerStats = []; // For additional leaderboards
    let playerRoles = {}; // For role filtering

    // Chart instances
    let pickupEloChartInstance = null;

    // DOM Elements
    const pickupEloChartCtx = document.getElementById('pickupEloChart')?.getContext('2d');
    const pickupEloTableBody = document.getElementById('pickupEloTable')?.querySelector('tbody');

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
        enhanceChartInteractivity(pickupEloChartInstance);
        addChartControls('pickupEloChart');
        
        console.log("Pickup Player ELO Chart rendered.");
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

    function renderPickupEloTable() {
        console.log("Rendering Pickup Player ELO Table...");
        if (!pickupEloTableBody || !pickupEloLadder || pickupEloLadder.length === 0) {
            console.warn("Pickup ELO table body or data not available.");
            const table = document.getElementById('pickupEloTable');
            if (table && !table.querySelector('.no-data-message')) {
                const msgRow = table.insertRow();
                const cell = msgRow.insertCell();
                cell.colSpan = 6; // Span across all columns (including Role column)
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
            rankCell.classList.add('rank-cell');

            const nameCell = row.insertCell();
            nameCell.textContent = player.player_name;
            
            // Add role cell
            const roleCell = row.insertCell();
            const roleText = player.role || 'None';
            roleCell.textContent = roleText;
            // Add a data attribute for role filtering
            row.setAttribute('data-role', roleText);
            // Add debug class to make role cells stand out during debugging
            roleCell.classList.add('role-cell');

            const eloCell = row.insertCell();
            eloCell.textContent = player.elo_rating;

            const wlCell = row.insertCell();
            wlCell.textContent = `${player.matches_won}-${player.matches_lost}`;

            const winRateCell = row.insertCell();
            winRateCell.textContent = `${player.win_rate}%`;
        });
        console.log("Pickup Player ELO Table populated.");
    }

    // Function to apply interactive features to tables
    function applyTableInteractivity() {
        console.log("Applying pickup table interactivity features...");
        
        // Make pickup ELO table sortable
        makeTableSortable('pickupEloTable');
        addTableFilter('pickupEloTable', 'Search players...');
        enableTableRowSelection('pickupEloTable', (playerName) => {
            filterChartByName(pickupEloChartInstance, playerName);
        });
        
        // Add button event listener for showing all players
        const showAllButton = document.getElementById('showAllPlayersButton');
        if (showAllButton) {
            showAllButton.addEventListener('click', () => {
                filterChartByName(pickupEloChartInstance, null); // Clear filters
                
                // Clear any selected rows
                const selectedRows = document.querySelectorAll('#pickupEloTable tbody tr.selected');
                selectedRows.forEach(row => row.classList.remove('selected'));
            });
        }
        
        // CRITICAL FIX: Ensure the role filter container is visible and positioned correctly
        const roleFilterContainer = document.getElementById('roleFilterContainer');
        if (roleFilterContainer) {
            // Force visibility and positioning
            roleFilterContainer.style.display = 'flex';
            roleFilterContainer.style.flexWrap = 'wrap';
            roleFilterContainer.style.gap = '8px';
            roleFilterContainer.style.padding = '10px';
            roleFilterContainer.style.border = '3px solid #ff0000'; // Red border to make it obvious
            roleFilterContainer.style.backgroundColor = '#f8f8f8';
            roleFilterContainer.style.margin = '15px 0';
            roleFilterContainer.style.position = 'relative'; // Ensure it's in the normal flow
            roleFilterContainer.style.zIndex = '100'; // Ensure it's on top
            
            // Add a label at the top
            const label = document.createElement('div');
            label.textContent = 'ROLE FILTER BUTTONS:';
            label.style.fontWeight = 'bold';
            label.style.width = '100%';
            label.style.marginBottom = '10px';
            roleFilterContainer.prepend(label);
            
            console.log("Force-styled the role filter container");
        }
        
        // Add role filter if we have role data
        const uniqueRoles = new Set();
        
        // Debug: Check each player's role
        console.log("Checking roles for each player:");
        pickupEloLadder.forEach(player => {
            console.log(`  Player ${player.player_name}: role = "${player.role || 'null/undefined'}"`);
            if (player.role) {
                uniqueRoles.add(player.role);
            }
        });
        
        console.log(`Found ${uniqueRoles.size} unique roles: ${Array.from(uniqueRoles).join(', ')}`);
        
        // Only add role filter if we have role data
        if (uniqueRoles.size > 0) {
            console.log("Adding role filter buttons");
            addRoleFilter('pickupEloTable', Array.from(uniqueRoles));
            console.log(`Added role filter with ${uniqueRoles.size} roles: ${Array.from(uniqueRoles).join(', ')}`);

            // Connect role filter button clicks to filter all leaderboards
            document.addEventListener('roleFilterChanged', (e) => {
                const selectedRole = e.detail.role;
                console.log(`Filtering leaderboards for role: ${selectedRole}`);
                filterAllLeaderboards(selectedRole);
            });
        } else {
            console.log("No roles found, not adding role filter");
            
            // Even if we don't have roles in the data, let's add some default role buttons for testing
            console.log("Adding default role buttons for testing");
            addRoleFilter('pickupEloTable', ['Farmer', 'Flex', 'Support']);
        }
        
        
        // Add separate listener to filter leaderboards when role buttons are clicked
        if (roleFilterContainer) {
            // Use a flag to prevent adding the listener multiple times if this function is called again
            if (!roleFilterContainer.dataset.leaderboardListenerAdded) {
                roleFilterContainer.addEventListener('click', (e) => {
                    const target = e.target;
                    // Ensure it's a role button click
                    if (target.classList.contains('role-filter-button') && target.dataset.role) {
                        const selectedRole = target.dataset.role;
                        console.log(`Filtering leaderboards for role: ${selectedRole}`);
                        filterAllLeaderboards(selectedRole); // Call the leaderboard filter function
                    }
                });
                roleFilterContainer.dataset.leaderboardListenerAdded = 'true'; // Mark listener as added
                console.log("Added separate event listener for leaderboard role filtering.");
            }
        }
        
        console.log("Pickup table interactivity features applied.");
    }

    async function renderVisualizations() {
        try {
            console.log("Starting pickup visualization rendering...");

            // Call individual rendering functions
            renderPickupEloChart();
            renderPickupEloTable();
            
            // Apply interactivity
            applyTableInteractivity();
            await createAdditionalLeaderboards('#leaderboards-container', playerStats);
            
            console.log("All pickup visualizations rendered successfully");
        } catch (error) {
            console.error("Error rendering pickup visualizations:", error);
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
            console.log("Initializing pickup data...");
            
            // Set global flag to indicate pickup page
            window.isPickupPage = true;
            document.title = "Pickup Stats - Squadrons Visualizations"; // Force title to include pickup
            
            // Load real data
            const data = await loadAllRealData();
            
            // Validate that we have pickup data
            if (!data.pickupEloLadder || data.pickupEloLadder.length === 0) {
                console.error("No pickup ladder data loaded!");
                document.body.innerHTML += `
                    <div style="color: red; padding: 20px; margin: 20px; border: 1px solid red; background: #ffeeee;">
                        <h2>Pickup Data Not Found</h2>
                        <p>Could not load pickup ELO ladder data. Please ensure that pickup data has been generated.</p>
                        <p>Expected file: ../elo_reports_pickup/pickup_player_elo_ladder.json</p>
                    </div>
                `;
            }
            
            // Store data for use in rendering
            pickupEloHistory = data.pickupEloHistory;
            pickupEloLadder = data.pickupEloLadder;
            playerRoles = data.playerRoles;
            
            // Filter player stats to only include pickup-related stats
            // This ensures we don't show team player stats in pickup leaderboards
            if (data.playerStats && data.playerStats.length > 0) {
                // Create a set of pickup player names for filtering
                const pickupPlayerNames = new Set();
                
                if (pickupEloLadder && pickupEloLadder.length > 0) {
                    pickupEloLadder.forEach(player => {
                        pickupPlayerNames.add(player.player_name);
                    });
                    console.log(`Found ${pickupPlayerNames.size} unique pickup player names`);
                }
                
                // If we have pickup player names, filter stats to only include those players
                if (pickupPlayerNames.size > 0) {
                    playerStats = data.playerStats.filter(player => 
                        pickupPlayerNames.has(player.player_name)
                    );
                    console.log(`Filtered player stats from ${data.playerStats.length} to ${playerStats.length} pickup players`);
                } else {
                    // If we can't filter, just use all stats
                    playerStats = data.playerStats;
                    console.log(`Using all ${playerStats.length} player stats as pickup stats`);
                }
            } else {
                playerStats = [];
                console.log("No player stats data available for pickup");
            }
            
            console.log("Pickup data loaded successfully");
            console.log("Pickup ladder entries:", pickupEloLadder.length);
            console.log("Pickup history entries:", pickupEloHistory.length);
            
            // Debug: Examine roles in first 5 entries
            console.log("First 5 entries in pickup ladder with roles:", 
                pickupEloLadder.slice(0, 5).map(p => ({
                    name: p.player_name,
                    role: p.role,
                    elo: p.elo_rating
                }))
            );
            
            // Count roles
            const roleCounts = {};
            pickupEloLadder.forEach(player => {
                const role = player.role || 'None';
                roleCounts[role] = (roleCounts[role] || 0) + 1;
            });
            console.log("Role counts in ladder data:", roleCounts);
            
            // Render visualizations
            await renderVisualizations();
            
            console.log("Pickup page initialization complete");
        } catch (error) {
            console.error("Error initializing pickup data:", error);
            document.body.innerHTML += `
                <div style="color: red; padding: 20px; margin: 20px; border: 1px solid red; background: #ffeeee;">
                    <h2>Error Loading Pickup Data</h2>
                    <p>There was an error initializing the pickup data: ${error.message}</p>
                </div>
            `;
        }
    }

    // Start initialization
    initializeData();
}