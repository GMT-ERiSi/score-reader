/**
 * tableInteractivity.js
 * Handles all interactive features for leaderboard tables including sorting and filtering.
 */

// Make table headers sortable
function makeTableSortable(tableId) {
    const table = document.getElementById(tableId);
    if (!table) {
        console.warn(`Table with ID '${tableId}' not found.`);
        return;
    }

    const headers = table.querySelectorAll('thead th');
    const tableBody = table.querySelector('tbody');
    
    headers.forEach((header, index) => {
        // Skip the rank column (usually the first column)
        if (index === 0) return;
        
        // Add sort icon and styles
        header.classList.add('sortable');
        header.innerHTML = `${header.textContent} <span class="sort-icon">⇵</span>`;
        header.dataset.sortDirection = 'none'; // 'none', 'asc', or 'desc'
        
        // Add click event to toggle sort
        header.addEventListener('click', () => {
            // Update sort direction
            const currentDirection = header.dataset.sortDirection;
            const newDirection = currentDirection === 'asc' ? 'desc' : 'asc';
            
            // Reset all headers
            headers.forEach(h => {
                h.dataset.sortDirection = 'none';
                h.querySelector('.sort-icon')?.textContent = '⇵';
            });
            
            // Set new direction for clicked header
            header.dataset.sortDirection = newDirection;
            header.querySelector('.sort-icon').textContent = newDirection === 'asc' ? '↑' : '↓';
            
            // Sort the table
            sortTable(tableBody, index, newDirection);
        });
    });
}

// Sort the table based on a column and direction
function sortTable(tableBody, columnIndex, direction) {
    const rows = Array.from(tableBody.querySelectorAll('tr'));
    
    // Sort rows based on the content of the specified column
    rows.sort((a, b) => {
        const aValue = getCellValue(a, columnIndex);
        const bValue = getCellValue(b, columnIndex);
        
        // If comparing numbers (like ELO rating)
        if (!isNaN(aValue) && !isNaN(bValue)) {
            return direction === 'asc' ? aValue - bValue : bValue - aValue;
        }
        
        // If comparing text (like names)
        return direction === 'asc' 
            ? aValue.localeCompare(bValue) 
            : bValue.localeCompare(aValue);
    });
    
    // Re-append rows in the sorted order
    rows.forEach(row => tableBody.appendChild(row));
    
    // Update rank numbers if they exist
    updateRankNumbers(tableBody);
}

// Get cell value for comparison
function getCellValue(row, index) {
    const cell = row.cells[index];
    if (!cell) return '';
    
    // Get raw text content
    let value = cell.textContent.trim();
    
    // Parse numbers, including percentage values
    if (value.endsWith('%')) {
        return parseFloat(value);
    }
    
    // Handle W-L format (like "10-5")
    if (value.match(/^\d+-\d+$/)) {
        const [wins, losses] = value.split('-').map(Number);
        return wins / (wins + losses); // Win ratio as the sortable value
    }
    
    // Return as number if numeric, otherwise as string
    return isNaN(value) ? value : parseFloat(value);
}

// Update rank numbers after sorting
function updateRankNumbers(tableBody) {
    const rows = tableBody.querySelectorAll('tr');
    rows.forEach((row, index) => {
        // If first cell is the rank, update it
        if (row.cells[0] && row.cells[0].classList.contains('rank-cell')) {
            row.cells[0].textContent = index + 1;
        }
    });
}

// Add a search filter above the table
function addTableFilter(tableId, placeholderText = 'Search...') {
    const table = document.getElementById(tableId);
    if (!table) {
        console.warn(`Table with ID '${tableId}' not found.`);
        return;
    }
    
    // Create filter components
    const filterContainer = document.createElement('div');
    filterContainer.className = 'table-filter';
    
    const filterInput = document.createElement('input');
    filterInput.type = 'text';
    filterInput.placeholder = placeholderText;
    filterInput.className = 'filter-input';
    
    const clearButton = document.createElement('button');
    clearButton.textContent = 'Clear';
    clearButton.className = 'clear-filter';
    clearButton.addEventListener('click', () => {
        filterInput.value = '';
        filterTable(table, ''); // Clear filter
    });
    
    // Add elements to container
    filterContainer.appendChild(filterInput);
    filterContainer.appendChild(clearButton);
    
    // Insert before the table
    table.parentNode.insertBefore(filterContainer, table);
    
    // Add event listener for filtering
    filterInput.addEventListener('input', (e) => {
        const filterText = e.target.value.toLowerCase();
        filterTable(table, filterText);
    });
}

// Filter table rows based on search text
function filterTable(table, filterText) {
    const rows = table.querySelectorAll('tbody tr');
    let visibleCount = 0;
    
    rows.forEach(row => {
        const cells = Array.from(row.cells).slice(1); // Skip rank column
        const containsText = cells.some(cell => 
            cell.textContent.toLowerCase().includes(filterText)
        );
        
        if (containsText || filterText === '') {
            row.style.display = '';
            visibleCount++;
        } else {
            row.style.display = 'none';
        }
    });
    
    // Show/hide "no results" message
    let noResultsMsg = table.parentNode.querySelector('.no-results-message');
    
    if (visibleCount === 0 && filterText !== '') {
        if (!noResultsMsg) {
            noResultsMsg = document.createElement('p');
            noResultsMsg.className = 'no-results-message';
            noResultsMsg.textContent = 'No matching results found.';
            table.parentNode.insertBefore(noResultsMsg, table.nextSibling);
        }
        noResultsMsg.style.display = 'block';
    } else if (noResultsMsg) {
        noResultsMsg.style.display = 'none';
    }
}

// Make a table row clickable to filter the chart
function enableTableRowSelection(tableId, chartFilterCallback) {
    const table = document.getElementById(tableId);
    if (!table) {
        console.warn(`Table with ID '${tableId}' not found.`);
        return;
    }
    
    const tbody = table.querySelector('tbody');
    if (!tbody) {
        console.warn(`Table body not found for table '${tableId}'.`);
        return;
    }
    
    // Add selection capability to rows
    tbody.addEventListener('click', (e) => {
        const row = e.target.closest('tr');
        if (!row) return;
        
        // Toggle selected state
        if (row.classList.contains('selected')) {
            // Deselect this row
            row.classList.remove('selected');
            chartFilterCallback(null); // Reset filter
        } else {
            // Deselect any previously selected rows
            tbody.querySelectorAll('tr.selected').forEach(r => r.classList.remove('selected'));
            
            // Select clicked row
            row.classList.add('selected');
            
            // Get name (assuming it's in the second column)
            const name = row.cells[1]?.textContent;
            if (name) {
                chartFilterCallback(name);
            }
        }
    });
    
    // Add a "Show All" button above the table
    const showAllButton = document.createElement('button');
    showAllButton.textContent = 'Show All in Chart';
    showAllButton.className = 'show-all-button';
    showAllButton.addEventListener('click', () => {
        // Remove all selections
        tbody.querySelectorAll('tr.selected').forEach(r => r.classList.remove('selected'));
        chartFilterCallback(null); // Reset chart to show all
    });
    
    // Add the button above the table
    const buttonContainer = document.createElement('div');
    buttonContainer.className = 'chart-controls';
    buttonContainer.appendChild(showAllButton);
    
    // Add tooltip for user guidance
    const tooltip = document.createElement('div');
    tooltip.className = 'tooltip';
    tooltip.textContent = 'Click on a row to filter the chart';
    buttonContainer.appendChild(tooltip);
    
    table.parentNode.insertBefore(buttonContainer, table);
}

// Export all functions
export {
    makeTableSortable,
    addTableFilter,
    enableTableRowSelection
};