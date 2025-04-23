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
                const icon = h.querySelector('.sort-icon');
                if (icon) { icon.textContent = '⇵'; }
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

// Make a table row clickable to filter the chart - allows multiple selections
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
    
    // Track selected items
    const selectedNames = new Set();
    
    // Add selection capability to rows
    tbody.addEventListener('click', (e) => {
        const row = e.target.closest('tr');
        if (!row) return;
        
        // Toggle selected state
        if (row.classList.contains('selected')) {
            // Deselect this row
            row.classList.remove('selected');
            
            // Get name and remove from selected set
            const name = row.cells[1]?.textContent;
            if (name) {
                selectedNames.delete(name);
            }
        } else {
            // Select clicked row (without deselecting others)
            row.classList.add('selected');
            
            // Get name and add to selected set
            const name = row.cells[1]?.textContent;
            if (name) {
                selectedNames.add(name);
            }
        }
        
        // Update chart with all selected names
        chartFilterCallback(selectedNames.size > 0 ? Array.from(selectedNames) : null);
    });
}

// Add a role filter with buttons above the table
function addRoleFilter(tableId, roles = ['Farmer', 'Flex', 'Support'], containerId = 'roleFilterContainer') {
    const table = document.getElementById(tableId);
    if (!table) {
        console.warn(`Table with ID '${tableId}' not found.`);
        return;
    }
    
    // Get the role filter container
    const roleFilterContainer = document.getElementById(containerId);
    if (!roleFilterContainer) {
        console.warn(`Role filter container '${containerId}' not found.`);
        return;
    }
    
    console.log(`Adding role filter buttons for ${roles.length} roles to container '${containerId}': ${JSON.stringify(roles)}`);
    
    // Clear any existing content
    roleFilterContainer.innerHTML = '';
    
    // Add heading
    const heading = document.createElement('h4');
    heading.textContent = 'Filter Players by Role';
    heading.style.marginTop = '0';
    heading.style.marginBottom = '10px';
    heading.style.color = '#333';
    roleFilterContainer.appendChild(heading);
    
    // Create button container
    const buttonContainer = document.createElement('div');
    buttonContainer.style.display = 'flex';
    buttonContainer.style.flexWrap = 'wrap';
    buttonContainer.style.gap = '8px';
    roleFilterContainer.appendChild(buttonContainer);
    
    // Add 'All' button (selected by default)
    const allButton = document.createElement('button');
    allButton.textContent = 'All Roles';
    allButton.className = 'role-filter-button active';
    allButton.style.padding = '8px 15px';
    allButton.style.margin = '4px';
    allButton.style.backgroundColor = '#0066cc';
    allButton.style.color = 'white';
    allButton.style.border = '1px solid #0055aa';
    allButton.style.borderRadius = '4px';
    allButton.style.cursor = 'pointer';
    allButton.style.fontWeight = 'bold';
    allButton.dataset.role = 'all';
    buttonContainer.appendChild(allButton);
    
    // Add role buttons
    roles.forEach(role => {
        const button = document.createElement('button');
        button.textContent = role;
        button.className = 'role-filter-button';
        button.style.padding = '8px 15px';
        button.style.margin = '4px';
        button.style.backgroundColor = '#f2f2f2';
        button.style.border = '1px solid #ddd';
        button.style.borderRadius = '4px';
        button.style.cursor = 'pointer';
        button.style.fontWeight = 'bold';
        button.dataset.role = role;
        buttonContainer.appendChild(button);
        console.log(`Added button for role: ${role}`);
    });
    
    // Add 'None' button for players without a role
    const noneButton = document.createElement('button');
    noneButton.textContent = 'No Role';
    noneButton.className = 'role-filter-button';
    noneButton.style.padding = '8px 15px';
    noneButton.style.margin = '4px';
    noneButton.style.backgroundColor = '#f2f2f2';
    noneButton.style.border = '1px solid #ddd';
    noneButton.style.borderRadius = '4px';
    noneButton.style.cursor = 'pointer';
    noneButton.style.fontWeight = 'bold';
    noneButton.dataset.role = 'none';
    buttonContainer.appendChild(noneButton);
    
    // Add event listener to the container (event delegation)
    roleFilterContainer.addEventListener('click', (e) => {
        const target = e.target;
        
        // Only handle button clicks
        if (!target.classList.contains('role-filter-button')) {
            return;
        }
        
        console.log(`Role filter button clicked: ${target.dataset.role}`);
        
        // Remove 'active' class from all buttons
        roleFilterContainer.querySelectorAll('.role-filter-button').forEach(btn => {
            btn.classList.remove('active');
            btn.style.backgroundColor = '#f2f2f2';
            btn.style.color = '#333';
        });
        
        // Add 'active' class to the clicked button
        target.classList.add('active');
        target.style.backgroundColor = '#0066cc';
        target.style.color = 'white';
        
        // Filter the table
        filterTableByRole(table, target.dataset.role);
    });
    
    console.log(`Role filter added with ${roles.length} roles: ${roles.join(', ')}`);
    return roleFilterContainer;
}

// Filter table rows based on selected role
function filterTableByRole(table, roleFilter) {
    const rows = table.querySelectorAll('tbody tr');
    let visibleCount = 0;
    
    // Get the role column index (typically 2nd column for pickup player tables, after Player Name)
    let roleColumnIndex = 2; // Default role column index
    
    // Check if there's a role column header to be sure
    const headers = table.querySelectorAll('thead th');
    headers.forEach((header, index) => {
        if (header.textContent.trim().toLowerCase() === 'role') {
            roleColumnIndex = index;
        }
    });
    
    console.log(`Filtering by role: ${roleFilter}, using column index: ${roleColumnIndex}`);
    
    // Apply filter
    rows.forEach(row => {
        const cells = row.cells;
        if (cells.length <= roleColumnIndex) {
            // Row doesn't have enough columns, show it
            row.style.display = '';
            visibleCount++;
            return;
        }
        
        const roleCell = cells[roleColumnIndex];
        const roleText = roleCell ? roleCell.textContent.trim() : '';
        
        console.log(`Row role text: "${roleText}", comparing to filter: "${roleFilter}"`);
        
        if (roleFilter === 'all' || 
            (roleFilter === 'none' && (roleText === '' || roleText.toLowerCase() === 'none')) ||
            (roleText.toLowerCase().includes(roleFilter.toLowerCase()))) {
            row.style.display = '';
            visibleCount++;
        } else {
            row.style.display = 'none';
        }
    });
    
    console.log(`Filter result: ${visibleCount} visible rows`);
    
    // Show/hide "no results" message
    let noResultsMsg = table.parentNode.querySelector('.no-results-message');
    
    if (visibleCount === 0) {
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
    
    // Update rank numbers for visible rows
    updateRankNumbersForVisible(table);
}

// Update rank numbers for visible rows only
function updateRankNumbersForVisible(table) {
    const rows = table.querySelectorAll('tbody tr');
    let visibleIndex = 1;
    
    rows.forEach(row => {
        if (row.style.display !== 'none' && row.cells[0] && row.cells[0].classList.contains('rank-cell')) {
            row.cells[0].textContent = visibleIndex++;
        }
    });
}

// Export all functions
export {
    makeTableSortable,
    addTableFilter,
    enableTableRowSelection,
    addRoleFilter,
    filterTableByRole,
    updateRankNumbersForVisible // Export this function
};