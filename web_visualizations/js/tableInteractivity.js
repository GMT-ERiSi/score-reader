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
    
    // Add control buttons
    const buttonContainer = document.createElement('div');
    buttonContainer.className = 'chart-controls';
    
    // Show All button
    const showAllButton = document.createElement('button');
    showAllButton.textContent = 'Show All in Chart';
    showAllButton.className = 'show-all-button';
    showAllButton.addEventListener('click', () => {
        // Remove all selections
        tbody.querySelectorAll('tr.selected').forEach(r => r.classList.remove('selected'));
        selectedNames.clear();
        chartFilterCallback(null); // Reset chart to show all
    });
    
    // Select All button
    const selectAllButton = document.createElement('button');
    selectAllButton.textContent = 'Select All Rows';
    selectAllButton.className = 'select-all-button';
    selectAllButton.addEventListener('click', () => {
        const rows = tbody.querySelectorAll('tr');
        const allNames = [];
        
        rows.forEach(row => {
            row.classList.add('selected');
            const name = row.cells[1]?.textContent;
            if (name) {
                selectedNames.add(name);
                allNames.push(name);
            }
        });
        
        chartFilterCallback(allNames);
    });
    
    // Add buttons to container
    buttonContainer.appendChild(selectAllButton);
    buttonContainer.appendChild(showAllButton);
    
    // Add tooltip for user guidance
    const tooltip = document.createElement('div');
    tooltip.className = 'tooltip';
    tooltip.textContent = 'Click on rows to filter the chart (multiple selections allowed)';
    buttonContainer.appendChild(tooltip);
    
    table.parentNode.insertBefore(buttonContainer, table);
}

// Add a role filter dropdown above the table
function addRoleFilter(tableId, roles = ['Farmer', 'Flex', 'Support']) {
    const table = document.getElementById(tableId);
    if (!table) {
        console.warn(`Table with ID '${tableId}' not found.`);
        return;
    }
    
    // Get the filter container if it exists, or create it
    let filterContainer = table.parentNode.querySelector('.table-filter');
    if (!filterContainer) {
        filterContainer = document.createElement('div');
        filterContainer.className = 'table-filter';
        table.parentNode.insertBefore(filterContainer, table);
    }
    
    // Create the role filter dropdown
    const roleFilterContainer = document.createElement('div');
    roleFilterContainer.className = 'role-filter';
    
    const roleLabel = document.createElement('label');
    roleLabel.textContent = 'Filter by Role: ';
    roleLabel.for = `${tableId}-role-filter`;
    
    const roleSelect = document.createElement('select');
    roleSelect.id = `${tableId}-role-filter`;
    roleSelect.className = 'role-filter-select';
    
    // Add 'All' option
    const allOption = document.createElement('option');
    allOption.value = 'all';
    allOption.textContent = 'All Roles';
    roleSelect.appendChild(allOption);
    
    // Add role options
    roles.forEach(role => {
        const option = document.createElement('option');
        option.value = role;
        option.textContent = role;
        roleSelect.appendChild(option);
    });
    
    // Add 'No Role' option
    const noRoleOption = document.createElement('option');
    noRoleOption.value = 'none';
    noRoleOption.textContent = 'No Role';
    roleSelect.appendChild(noRoleOption);
    
    // Add event listener
    roleSelect.addEventListener('change', () => {
        filterTableByRole(table, roleSelect.value);
    });
    
    // Add to container
    roleFilterContainer.appendChild(roleLabel);
    roleFilterContainer.appendChild(roleSelect);
    filterContainer.appendChild(roleFilterContainer);
    
    return roleSelect;
}

// Filter table rows based on selected role
function filterTableByRole(table, roleFilter) {
    const rows = table.querySelectorAll('tbody tr');
    let visibleCount = 0;
    
    // Get the role column index (typically 4th column for player tables)
    // First check if there's a role column header
    let roleColumnIndex = -1;
    const headers = table.querySelectorAll('thead th');
    headers.forEach((header, index) => {
        if (header.textContent.trim().toLowerCase() === 'role') {
            roleColumnIndex = index;
        }
    });
    
    // If we couldn't find a role column by header name, use a default column
    if (roleColumnIndex === -1) {
        // Try to find it by looking at row content - ELO tables typically have role in 3rd column
        const firstRow = rows[0];
        if (firstRow) {
            const cells = firstRow.cells;
            if (cells.length >= 3) {
                const possibleRoleCell = cells[2];
                const cellText = possibleRoleCell.textContent.trim();
                if (['farmer', 'flex', 'support', 'none', ''].includes(cellText.toLowerCase())) {
                    roleColumnIndex = 2; // Found the role column
                }
            }
        }
        
        // If we still can't find it, default to column 2
        if (roleColumnIndex === -1) {
            roleColumnIndex = 2;
        }
    }
    
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
        
        if (roleFilter === 'all' || 
            (roleFilter === 'none' && (roleText === '' || roleText.toLowerCase() === 'none' || roleText.toLowerCase() === 'unknown')) ||
            (roleText.toLowerCase() === roleFilter.toLowerCase())) {
            row.style.display = '';
            visibleCount++;
        } else {
            row.style.display = 'none';
        }
    });
    
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
    filterTableByRole
};