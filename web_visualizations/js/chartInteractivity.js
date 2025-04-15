/**
 * chartInteractivity.js
 * Handles enhanced chart interaction features including filtering, tooltips, and zoom/pan.
 */

// Enhance a Chart.js chart with additional interactive features
function enhanceChartInteractivity(chartInstance) {
    if (!chartInstance) {
        console.warn('Cannot enhance interactivity: Chart instance not provided');
        return;
    }

    console.log('Enhancing chart interactivity...');

    try {
        // Original chart options
        const originalOptions = chartInstance.config.options;
        
        // Enhance tooltip configuration
        chartInstance.config.options.plugins.tooltip = {
            ...originalOptions.plugins.tooltip,
            backgroundColor: 'rgba(0, 0, 0, 0.7)',
            titleFont: { size: 14, weight: 'bold' },
            bodyFont: { size: 13 },
            padding: 10,
            cornerRadius: 6,
            displayColors: true,
            mode: 'index',
            intersect: false,
            callbacks: {
                // Customize tooltip label
                label: function(context) {
                    const label = context.dataset.label || '';
                    const value = context.raw.y;
                    return `${label}: ${Math.round(value)}`;
                },
                // Customize tooltip title (usually the date)
                title: function(tooltipItems) {
                    // Convert timestamp to formatted date
                    const date = new Date(tooltipItems[0].parsed.x);
                    return date.toLocaleDateString('en-US', { 
                        year: 'numeric', 
                        month: 'short', 
                        day: 'numeric',
                        hour: '2-digit',
                        minute: '2-digit'
                    });
                }
            }
        };
        
        // Enhance interaction settings
        chartInstance.config.options.interaction = {
            ...originalOptions.interaction,
            mode: 'nearest',
            axis: 'x',
            intersect: false
        };
        
        // Check for Chart.js Zoom plugin
        if (typeof Chart !== 'undefined' && Chart.Zoom) {
            console.log('Chart.js Zoom plugin detected, enabling zoom features');
            chartInstance.config.options.plugins.zoom = {
                zoom: {
                    wheel: { enabled: true },
                    pinch: { enabled: true },
                    mode: 'x',
                    onZoom: () => console.log('Chart zoomed')
                },
                pan: {
                    enabled: true,
                    mode: 'x'
                }
            };
        } else {
            console.log('Chart.js Zoom plugin not detected, skipping zoom features');
        }
        
        // Apply changes
        chartInstance.update();
        console.log('Chart interactivity enhanced successfully');
    } catch (error) {
        console.error('Error enhancing chart interactivity:', error);
    }
}

// Filter chart data to show only selected team/player
function filterChartByName(chartInstance, nameToFilter) {
    if (!chartInstance) {
        console.warn('Cannot filter: Chart instance not provided');
        return;
    }
    
    try {
        console.log(`Filtering chart to ${nameToFilter ? `show only: ${nameToFilter}` : 'show all data'}`);
        
        // Store original datasets if not already stored
        if (!chartInstance._originalDatasets) {
            chartInstance._originalDatasets = [...chartInstance.data.datasets];
        }
        
        // If nameToFilter is null, show all datasets
        if (nameToFilter === null) {
            chartInstance.data.datasets = [...chartInstance._originalDatasets];
            chartInstance.update();
            return;
        }
        
        // Filter datasets to show only the selected name
        const filteredDatasets = chartInstance._originalDatasets.filter(dataset => 
            dataset.label === nameToFilter
        );
        
        if (filteredDatasets.length === 0) {
            console.warn(`No dataset found with label '${nameToFilter}'`);
            return;
        }
        
        // Apply filtered datasets
        chartInstance.data.datasets = filteredDatasets;
        chartInstance.update();
    } catch (error) {
        console.error('Error filtering chart:', error);
    }
}

// Add reset zoom button to chart container
function addChartControls(chartId) {
    const chartCanvas = document.getElementById(chartId);
    if (!chartCanvas) {
        console.warn(`Chart canvas with ID '${chartId}' not found.`);
        return;
    }
    
    try {
        const container = chartCanvas.parentElement;
        
        // Create control container
        const controlsContainer = document.createElement('div');
        controlsContainer.className = 'chart-controls';
        
        // Add reset zoom button if Chart.js Zoom plugin is available
        if (typeof Chart !== 'undefined' && Chart.Zoom) {
            const resetZoomButton = document.createElement('button');
            resetZoomButton.textContent = 'Reset Zoom';
            resetZoomButton.className = 'reset-zoom-button';
            resetZoomButton.addEventListener('click', () => {
                // Get chart instance from Chart.js registry
                const chartInstance = Chart.getChart(chartId);
                if (chartInstance) {
                    chartInstance.resetZoom();
                }
            });
            
            controlsContainer.appendChild(resetZoomButton);
        }
        
        // Insert the controls before the chart
        container.insertBefore(controlsContainer, chartCanvas);
        console.log(`Chart controls added for ${chartId}`);
    } catch (error) {
        console.error('Error adding chart controls:', error);
    }
}

// Export functions
export {
    enhanceChartInteractivity,
    filterChartByName,
    addChartControls
};