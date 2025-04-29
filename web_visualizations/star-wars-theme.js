// Star Wars theme enhancements for Squadrons Stats Visualizations

// Function to initialize Star Wars theme
function initializeStarWarsTheme() {
    console.log('Initializing Star Wars theme...');
    
    // Configure Chart.js global defaults for Star Wars theme
    Chart.defaults.color = '#e0e0e0';
    Chart.defaults.borderColor = 'rgba(60, 60, 65, 0.7)';
    Chart.defaults.font.family = "'Exo 2', sans-serif";
    
    // Custom tooltip styling
    Chart.defaults.plugins.tooltip.backgroundColor = 'rgba(20, 20, 25, 0.9)';
    Chart.defaults.plugins.tooltip.titleColor = '#ff3a30';
    Chart.defaults.plugins.tooltip.bodyColor = '#e0e0e0';
    Chart.defaults.plugins.tooltip.borderColor = '#ff3a30';
    Chart.defaults.plugins.tooltip.borderWidth = 1;
    Chart.defaults.plugins.tooltip.boxPadding = 5;
    
    // Custom legend styling
    Chart.defaults.plugins.legend.labels.color = '#e0e0e0';
    
    // Remove loading indicator when data is ready
    window.addEventListener('data-loaded', () => {
        const loadingContainer = document.getElementById('loading');
        if (loadingContainer) {
            loadingContainer.style.display = 'none';
        }
    });
    
    // Initialize faction data if we're on the team page
    if (window.isTeamPage) {
        initializeFactionData();
    }
    
    console.log('Star Wars theme initialized');
}

// Custom color function for Star Wars theme
function getStarWarsColor(index) {
    // Star Wars color palette
    const colors = [
        '#ff3a30', // Imperial Red
        '#60a4f8', // Rebel Blue
        '#22e774', // Green (like lightsaber)
        '#e2e246', // Yellow (like C-3PO)
        '#9e4bff', // Purple (like Mace Windu's lightsaber)
        '#ff8a1e', // Orange (like BB-8)
        '#00e8fe', // Cyan (like hologram)
        '#ff4693'  // Pink (like some blaster bolts)
    ];
    
    return colors[index % colors.length];
}

// Override the default getRandomColor function
function getRandomColor(index) {
    if (index !== undefined) {
        return getStarWarsColor(index);
    }
    
    // If no index provided, use the default Star Wars palette with random selection
    const colors = [
        '#ff3a30', '#60a4f8', '#22e774', '#e2e246', 
        '#9e4bff', '#ff8a1e', '#00e8fe', '#ff4693'
    ];
    return colors[Math.floor(Math.random() * colors.length)];
}

// Initialize faction comparison data (for team page)
function initializeFactionData() {
    console.log('Initializing faction comparison data...');
    
    // Get elements
    const imperialWinRate = document.getElementById('imperialWinRate');
    const imperialAvgElo = document.getElementById('imperialAvgElo');
    const rebelWinRate = document.getElementById('rebelWinRate');
    const rebelAvgElo = document.getElementById('rebelAvgElo');
    
    // Process team data to calculate faction stats
    if (window.teamEloHistory && window.teamEloHistory.length > 0) {
        let imperialWins = 0;
        let imperialMatches = 0;
        let rebelWins = 0;
        let rebelMatches = 0;
        
        // Count faction wins
        window.teamEloHistory.forEach(match => {
            if (match.winner === 'IMPERIAL') {
                imperialWins++;
            } else if (match.winner === 'REBEL') {
                rebelWins++;
            }
            imperialMatches++;
            rebelMatches++;
        });
        
        // Calculate win rates
        const impWinRateValue = imperialMatches > 0 ? ((imperialWins / imperialMatches) * 100).toFixed(1) : 0;
        const rebWinRateValue = rebelMatches > 0 ? ((rebelWins / rebelMatches) * 100).toFixed(1) : 0;
        
        // Calculate average ELO by faction
        let imperialEloSum = 0;
        let imperialTeamCount = 0;
        let rebelEloSum = 0;
        let rebelTeamCount = 0;
        
        // Extract unique teams by faction and get their latest ELO
        const imperialTeams = new Map();
        const rebelTeams = new Map();
        
        window.teamEloHistory.forEach(match => {
            imperialTeams.set(match.imperial.team_id, match.imperial.new_rating);
            rebelTeams.set(match.rebel.team_id, match.rebel.new_rating);
        });
        
        // Calculate average ELO for each faction
        imperialTeams.forEach(elo => {
            imperialEloSum += elo;
            imperialTeamCount++;
        });
        
        rebelTeams.forEach(elo => {
            rebelEloSum += elo;
            rebelTeamCount++;
        });
        
        const impAvgEloValue = imperialTeamCount > 0 ? Math.round(imperialEloSum / imperialTeamCount) : 0;
        const rebAvgEloValue = rebelTeamCount > 0 ? Math.round(rebelEloSum / rebelTeamCount) : 0;
        
        // Update UI
        if (imperialWinRate) imperialWinRate.textContent = `${impWinRateValue}%`;
        if (imperialAvgElo) imperialAvgElo.textContent = impAvgEloValue;
        if (rebelWinRate) rebelWinRate.textContent = `${rebWinRateValue}%`;
        if (rebelAvgElo) rebelAvgElo.textContent = rebAvgEloValue;
    } else {
        // Display dummy data if no match history is available
        if (imperialWinRate) imperialWinRate.textContent = '55.2%';
        if (imperialAvgElo) imperialAvgElo.textContent = '1024';
        if (rebelWinRate) rebelWinRate.textContent = '44.8%';
        if (rebelAvgElo) rebelAvgElo.textContent = '976';
    }
    
    console.log('Faction comparison data initialized');
}

// When the document is fully loaded
document.addEventListener('DOMContentLoaded', () => {
    console.log('DOM loaded, initializing Star Wars theme...');
    
    // Initialize theme
    initializeStarWarsTheme();
    
    // Modify chart rendering functions to use Star Wars colors
    const originalRenderTeamEloChart = window.renderTeamEloChart;
    const originalRenderPickupEloChart = window.renderPickupEloChart;
    
    if (originalRenderTeamEloChart) {
        window.renderTeamEloChart = function() {
            console.log('Calling enhanced team chart rendering with Star Wars theme...');
            
            // Call the original function
            originalRenderTeamEloChart();
            
            // Apply additional styling to the chart if it exists
            if (window.teamEloChartInstance) {
                // Update colors to use Star Wars palette
                window.teamEloChartInstance.data.datasets.forEach((dataset, index) => {
                    dataset.borderColor = getStarWarsColor(index);
                    dataset.pointBackgroundColor = getStarWarsColor(index);
                });
                
                // Update the chart
                window.teamEloChartInstance.update();
            }
        };
    }
    
    if (originalRenderPickupEloChart) {
        window.renderPickupEloChart = function() {
            console.log('Calling enhanced pickup chart rendering with Star Wars theme...');
            
            // Call the original function
            originalRenderPickupEloChart();
            
            // Apply additional styling to the chart if it exists
            if (window.pickupEloChartInstance) {
                // Update colors to use Star Wars palette
                window.pickupEloChartInstance.data.datasets.forEach((dataset, index) => {
                    dataset.borderColor = getStarWarsColor(index);
                    dataset.pointBackgroundColor = getStarWarsColor(index);
                });
                
                // Update the chart
                window.pickupEloChartInstance.update();
            }
        };
    }
    
    console.log('Star Wars theme initialization and function overrides completed');
});

// Dispatch an event when data is loaded
window.addEventListener('load', () => {
    // Simulate data loading delay for effect (remove in production)
    setTimeout(() => {
        const event = new Event('data-loaded');
        window.dispatchEvent(event);
    }, 1500);
});