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
    let flexEloLadder = [];    
    let supportEloLadder = []; 
    let farmerEloLadder = [];  
    let currentLadder = 'general'; // Add this line to track which ladder is shown
    let playerStats = []; // For additional leaderboards
    let playerRoles = {}; // For role filtering
    let tableInteractivityApplied = false; // Initialize to false

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
        const playersData = {}; // { player_id: { name: 'Player Name', data: [{x: index, y: rating}] } }
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
    
    // Function to filter chart by player role
    function filterChartByRole(chartInstance, role, ladderData) {
        if (!chartInstance) {
            console.warn('Cannot filter: Chart instance not provided');
            return;
        }
        
        try {
            // Store original datasets if not already stored
            if (!chartInstance._originalDatasets) {
                chartInstance._originalDatasets = [...chartInstance.data.datasets];
            }
            
            // If role is 'all', show all datasets
            if (role === 'all') {
                console.log('Role filter "All Roles" selected - resetting chart to show all pilots');
                
                // Ensure we have a deep copy of the original datasets
                chartInstance.data.datasets = JSON.parse(JSON.stringify(chartInstance._originalDatasets));
                chartInstance.update();
                
                // Verify the reset was successful
                console.log(`Chart reset complete: now showing ${chartInstance.data.datasets.length} datasets`);
                
                // Update filter status message
                updateChartFilterMessage('Showing all pilots');
                return;
            }
            
            console.log(`Filtering chart to show players with role: ${role}`);
            
            // Get player names with the selected role
            const playersWithRole = role === 'none' 
                ? ladderData.filter(player => !player.role || player.role.toLowerCase() === 'none').map(player => player.player_name)
                : ladderData.filter(player => player.role && player.role.toLowerCase() === role.toLowerCase()).map(player => player.player_name);
            
            console.log(`Found ${playersWithRole.length} players with role ${role}: ${playersWithRole.join(', ')}`);
            
            // Filter datasets to show only the selected players
            const filteredDatasets = chartInstance._originalDatasets.filter(dataset => 
                playersWithRole.includes(dataset.label)
            );
            
            if (filteredDatasets.length === 0) {
                console.warn(`No datasets found matching the selected role: ${role}`);
                // If no matching datasets, show a message but don't clear the chart
                updateChartFilterMessage(`No pilots found with role: ${role}`);
                return;
            }
            
            // Apply filtered datasets
            chartInstance.data.datasets = filteredDatasets;
            chartInstance.update();
            
            // Update filter status message
            updateChartFilterMessage(`Showing pilots with role: ${role}`);
        } catch (error) {
            console.error('Error filtering chart by role:', error);
        }
    }
    
    // Function to update the chart filter message
    function updateChartFilterMessage(message) {
        const chartContainer = document.querySelector('.chart-container');
        if (!chartContainer) return;
        
        // Check if filter message already exists
        let filterMsg = chartContainer.querySelector('.chart-filter-message');
        
        if (!filterMsg) {
            // Create new message element
            filterMsg = document.createElement('div');
            filterMsg.className = 'chart-filter-message';
            filterMsg.style.textAlign = 'center';
            filterMsg.style.padding = '5px';
            filterMsg.style.marginTop = '10px';
            filterMsg.style.fontSize = '14px';
            filterMsg.style.color = '#999';
            filterMsg.style.fontStyle = 'italic';
            
            // Insert after the chart
            chartContainer.appendChild(filterMsg);
        }
        
        // Update message content
        filterMsg.textContent = message;
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

    function renderEloTable(ladderData) {
        console.log(`Rendering ${currentLadder} ELO Table...`);
        if (!pickupEloTableBody || !ladderData || ladderData.length === 0) {
            console.warn(`${currentLadder} ELO table body or data not available.`);
            const table = document.getElementById('pickupEloTable');
            if (table && !table.querySelector('.no-data-message')) {
                const msgRow = table.insertRow();
                const cell = msgRow.insertCell();
                cell.colSpan = 6;
                cell.textContent = `${currentLadder} ELO ladder data not available.`;
                cell.className = 'no-data-message';
                cell.style.textAlign = 'center';
            }
            return;
        }
        
        // Clear previous data
        pickupEloTableBody.innerHTML = '';
    
        // Ensure ladder is sorted by rank
        const sortedLadder = ladderData.sort((a, b) => a.rank - b.rank);
        
        // Populate table rows
        sortedLadder.forEach(player => {
            const row = pickupEloTableBody.insertRow();
    
            const rankCell = row.insertCell();
            rankCell.textContent = player.rank;
            rankCell.classList.add('rank-cell');
    
            const nameCell = row.insertCell();
            nameCell.textContent = player.player_name;
            
            const roleCell = row.insertCell();
            const roleText = player.role || 'None';
            roleCell.textContent = roleText;
            row.setAttribute('data-role', roleText);
            roleCell.classList.add('role-cell');
    
            const eloCell = row.insertCell();
            eloCell.textContent = player.elo_rating;
    
            const wlCell = row.insertCell();
            wlCell.textContent = `${player.matches_won}-${player.matches_lost}`;
    
            const winRateCell = row.insertCell();
            winRateCell.textContent = `${player.win_rate}%`;
        });
        
        console.log(`${currentLadder} ELO Table populated.`);
        
        // Reapply table interactivity
        // makeTableSortable('pickupEloTable');
        // addTableFilter('pickupEloTable', 'Search players...');
        // enableTableRowSelection('pickupEloTable', (playerName) => {
            // filterChartByName(pickupEloChartInstance, playerName);
        //});
    }

    // Add this function to handle ladder switching
    function switchLadder(ladderType) {
        currentLadder = ladderType;
        
        // Update active tab
        document.querySelectorAll('.ladder-tab').forEach(tab => {
            tab.classList.toggle('active', tab.dataset.ladder === ladderType);
        });
        
        // Get the ladder data based on the type
        let ladderData;
        switch (ladderType) {
            case 'flex':
                ladderData = flexEloLadder;
                break;
            case 'support':
                ladderData = supportEloLadder;
                break;
            case 'farmer':
                ladderData = farmerEloLadder;
                break;
            default:
                ladderData = pickupEloLadder;
                break;
        }
        
        // Update the table
        renderEloTable(ladderData);
    }

    // Function to apply interactive features to tables
    function applyTableInteractivity() {
        // Only apply table interactivity once
        if (tableInteractivityApplied) {
            return;
        }
        console.log("Applying pickup table interactivity features...");
        
        // Make pickup ELO table sortable
        makeTableSortable('pickupEloTable');
        // Removed addTableFilter call since we removed the search field
        enableTableRowSelection('pickupEloTable', (playerName) => {
            filterChartByName(pickupEloChartInstance, playerName);
        });
        
        // Add button event listener for showing all players
        const showAllButton = document.getElementById('showAllPlayersButton');
        if (showAllButton) {
            showAllButton.addEventListener('click', () => {
                // Reset all chart filters
                filterChartByName(pickupEloChartInstance, null);
                
                // Reset the role filter buttons to "All Roles"
                const allRolesButton = document.querySelector('.role-filter-button[data-role="all"]');
                if (allRolesButton) {
                    // Simulate a click on the All Roles button
                    allRolesButton.click();
                } else {
                    // If no 'all' button, just reset the chart and update the message
                    if (pickupEloChartInstance && pickupEloChartInstance._originalDatasets) {
                        pickupEloChartInstance.data.datasets = [...pickupEloChartInstance._originalDatasets];
                        pickupEloChartInstance.update();
                        updateChartFilterMessage('Showing all pilots');
                    }
                }
                
                // Clear any selected rows
                const selectedRows = document.querySelectorAll('#pickupEloTable tbody tr.selected');
                selectedRows.forEach(row => row.classList.remove('selected'));
                
                console.log('Chart reset to show all players');
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

            // Connect role filter button clicks to filter all leaderboards and chart
            document.addEventListener('roleFilterChanged', (e) => {
            const selectedRole = e.detail.role;
            console.log(`Filtering leaderboards and chart for role: ${selectedRole}`);
            filterAllLeaderboards(selectedRole);
                
            // Also filter the chart based on role
            filterChartByRole(pickupEloChartInstance, selectedRole, pickupEloLadder);
        });
        } else {
            console.log("No roles found, not adding role filter");
            
            // Even if we don't have roles in the data, let's add some default role buttons for testing
            console.log("Adding default role buttons for testing");
            addRoleFilter('pickupEloTable', ['Farmer', 'Flex', 'Support']);
        }
        
        
        // Add separate listener to filter leaderboards and chart when role buttons are clicked
        if (roleFilterContainer) {
            // Use a flag to prevent adding the listener multiple times if this function is called again
            if (!roleFilterContainer.dataset.leaderboardListenerAdded) {
                roleFilterContainer.addEventListener('click', (e) => {
                    const target = e.target;
                    // Ensure it's a role button click
                    if (target.classList.contains('role-filter-button') && target.dataset.role) {
                        const selectedRole = target.dataset.role;
                        console.log(`Filtering leaderboards and chart for role: ${selectedRole}`);
                        
                        // Filter the leaderboards
                        filterAllLeaderboards(selectedRole);
                        
                        // Filter the chart based on role
                        filterChartByRole(pickupEloChartInstance, selectedRole, pickupEloLadder);
                    }
                });
                roleFilterContainer.dataset.leaderboardListenerAdded = 'true'; // Mark listener as added
                console.log("Added separate event listener for role filtering.");
            }
        }
        
        console.log("Pickup table interactivity features applied.");

                // Add ladder tab event listeners
        document.querySelectorAll('.ladder-tab').forEach(tab => {
            tab.addEventListener('click', () => {
                const ladderType = tab.dataset.ladder;
                switchLadder(ladderType);
            });
        });

        // Check URL for initial tab selection
        const urlParams = new URLSearchParams(window.location.search);
        const initialLadder = urlParams.get('ladder');
        if (initialLadder && ['general', 'flex', 'support', 'farmer'].includes(initialLadder)) {
            switchLadder(initialLadder);
        } else {
            switchLadder('general'); // Default to general ladder
        }
        // Mark as applied
        tableInteractivityApplied = true;
    }

    async function renderVisualizations() {
        try {
            console.log("Starting pickup visualization rendering...");

            // Call individual rendering functions
            renderPickupEloChart();
            renderEloTable(pickupEloLadder);
            
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
            flexEloLadder = data.flexEloLadder;        
            supportEloLadder = data.supportEloLadder;  
            farmerEloLadder = data.farmerEloLadder;    
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