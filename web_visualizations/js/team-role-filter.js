            // Make sure the leaderboards container has the same max-width as our section
            const leaderboardsContainer = document.getElementById('leaderboards-container');
            if (leaderboardsContainer) {
                leaderboardsContainer.style.maxWidth = '1200px';
                leaderboardsContainer.style.margin = '2rem auto';
                leaderboardsContainer.style.padding = '0';
            }// team-role-filter.js
// This script directly handles role filtering for the team page leaderboards

(function() {
    // Function to run when the DOM is fully loaded
    function setupRoleFiltering() {
        console.log("Setting up direct role filtering...");
        
        // Make sure the leaderboards container has the same max-width as our section
        const leaderboardsContainer = document.getElementById('leaderboards-container');
        if (leaderboardsContainer) {
            leaderboardsContainer.style.maxWidth = '1200px';
            leaderboardsContainer.style.margin = '2rem auto';
            leaderboardsContainer.style.padding = '0';
        }
        
        // Wait for tables to be created
        function waitForTables() {
            const aiKillsTable = document.getElementById('aiKillsTable');
            const damageTable = document.getElementById('damageTable');
            const netKillsTable = document.getElementById('netKillsTable');
            const leastDeathsTable = document.getElementById('leastDeathsTable');
            
            if (!aiKillsTable && !damageTable && !netKillsTable && !leastDeathsTable) {
                console.log("Tables not found yet, waiting...");
                setTimeout(waitForTables, 500);
                return;
            }
            
            console.log("Tables found, setting up filtering...");
            
            // Direct implementation of filtering
            const filterByRole = (roleFilter) => {
                console.log(`Direct filtering with role: ${roleFilter}`);
                
                // Get all tables in the additional-leaderboards section
                const leaderboardTables = document.querySelectorAll('#additional-leaderboards table');
                
                leaderboardTables.forEach(table => {
                    const rows = table.querySelectorAll('tbody tr');
                    let visibleCount = 0;
                    
                    // When 'all' is selected, show all rows
                    if (roleFilter === 'all') {
                        console.log("Showing ALL rows - 'all' role filter selected");
                        rows.forEach(row => {
                            row.style.display = '';
                            visibleCount++;
                        });
                    } else {
                        // Otherwise filter by the selected role
                        rows.forEach(row => {
                            // Get the role value from the third column (index 2), which is the role column
                            const roleCell = row.querySelector('td:nth-child(3)');
                            const rowRole = roleCell ? roleCell.textContent.trim() : 'None';
                            
                            if ((roleFilter === 'none' && (rowRole === 'None' || rowRole === '')) ||
                                rowRole.toLowerCase() === roleFilter.toLowerCase()) {
                                // Show matching rows
                                row.style.display = '';
                                visibleCount++;
                            } else {
                                // Hide non-matching rows
                                row.style.display = 'none';
                            }
                        });
                    }
                    
                    // Update ranks for visible rows
                    let rank = 1;
                    rows.forEach(row => {
                        if (row.style.display !== 'none') {
                            const rankCell = row.querySelector('td:first-child');
                            if (rankCell) {
                                rankCell.textContent = rank++;
                            }
                        }
                    });
                    
                    // Show/hide "no results" message
                    let noResultsMsg = table.parentNode.querySelector('.no-results-message');
                    if (visibleCount === 0 && roleFilter !== 'all') {
                        if (!noResultsMsg) {
                            noResultsMsg = document.createElement('p');
                            noResultsMsg.className = 'no-results-message';
                            noResultsMsg.textContent = `No players found for role: ${roleFilter}`;
                            noResultsMsg.style.color = '#ff3a30';
                            noResultsMsg.style.fontStyle = 'italic';
                            noResultsMsg.style.textAlign = 'center';
                            noResultsMsg.style.padding = '10px';
                            table.parentNode.insertBefore(noResultsMsg, table.nextSibling);
                        } else {
                            noResultsMsg.style.display = 'block';
                        }
                    } else if (noResultsMsg) {
                        noResultsMsg.style.display = 'none';
                    }
                });
                
                // Debug log the counts
                if (roleFilter === 'all') {
                    console.log('Showing ALL players as "All Roles" was selected');
                }
            };
            
            // Direct function to reset all buttons to inactive state
            function resetAllButtons() {
                document.querySelectorAll('.role-filter-button').forEach(btn => {
                    btn.classList.remove('active');
                    btn.style.backgroundColor = '#333333';
                    btn.style.color = '#e0e0e0';
                });
                
                // Make sure the All Roles button is properly styled when reset occurs
                const allButton = document.querySelector('.role-filter-button[data-role="all"]');
                if (allButton) {
                    allButton.classList.add('active');
                    allButton.style.backgroundColor = '#0066cc';
                    allButton.style.color = 'white';
                }
            }
            
            // Remove any existing click handlers by replacing the buttons
            const roleFilterContainer = document.getElementById('roleFilterContainer');
            if (roleFilterContainer) {
                const buttonContainer = document.getElementById('roleButtonContainer');
                if (buttonContainer) {
                    // Clone the button container to remove all event listeners
                    const newButtonContainer = buttonContainer.cloneNode(true);
                    buttonContainer.parentNode.replaceChild(newButtonContainer, buttonContainer);
                    
                    // Add click handlers to the fresh buttons
                    newButtonContainer.querySelectorAll('.role-filter-button').forEach(button => {
                        button.addEventListener('click', function() {
                            // Get the role from the button
                            const role = this.getAttribute('data-role');
                            console.log(`Role button clicked: ${role}`);
                            
                            // First reset all buttons
                            resetAllButtons();
                            
                            // Then activate only the clicked button
                            this.classList.add('active');
                            this.style.backgroundColor = '#0066cc';
                            this.style.color = 'white';
                            
                            // Special case for 'All Roles' button to ensure full reset
                            if (role === 'all') {
                                console.log('All Roles button clicked - forcing full table reset');
                            }
                            
                            // Apply filtering
                            filterByRole(role);
                        });
                    });
                    
                    console.log("Direct role filtering setup complete");
                }
            }
        }
        
        // Start waiting for tables
        waitForTables();
    }
    
    // Run on page load
    if (document.readyState === 'complete' || document.readyState === 'interactive') {
        setupRoleFiltering();
    } else {
        document.addEventListener('DOMContentLoaded', setupRoleFiltering);
    }
    
    // Also run after a short delay to make sure everything is loaded
    setTimeout(setupRoleFiltering, 2000);
})();
