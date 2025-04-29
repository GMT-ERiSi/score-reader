// This script removes search fields and properly centers the Show All buttons
(function() {
    // Function to run when the DOM is fully loaded
    function removeSearchFields() {
        console.log("Running search field cleanup...");
        
        // Make sure the role filter container is visible with proper styling
        const roleFilterContainer = document.getElementById('roleFilterContainer');
        if (roleFilterContainer) {
            roleFilterContainer.style.display = 'block';
            roleFilterContainer.style.border = '2px solid #555';
            roleFilterContainer.style.padding = '15px';
            roleFilterContainer.style.margin = '20px 0';
            roleFilterContainer.style.backgroundColor = 'rgba(40, 40, 45, 0.7)';
            roleFilterContainer.style.borderRadius = '8px';
            roleFilterContainer.style.boxShadow = '0 0 15px rgba(0, 0, 0, 0.3)';
            
            // Make sure the h4 title has white text
            const heading = roleFilterContainer.querySelector('h4');
            if (heading) {
                heading.style.color = '#ffffff';
            }
            
            console.log("Styled role filter container:", roleFilterContainer);
        }
        
        // Remove any search input fields
        const searchInputs = document.querySelectorAll('input[placeholder="Search pilots..."], input[placeholder="Search squadrons..."]');
        searchInputs.forEach(input => {
            const container = input.closest('.table-filter');
            if (container) {
                console.log("Removing search container:", container);
                container.parentNode.removeChild(container);
            } else {
                console.log("Removing search input:", input);
                input.parentNode.removeChild(input);
            }
        });
        
        // Get all container elements with class .table-filter
        const tableFilters = document.querySelectorAll('.table-filter');
        tableFilters.forEach(filter => {
            console.log("Removing table filter container:", filter);
            filter.parentNode.removeChild(filter);
        });
        
        // Center Show All buttons
        const showAllButtons = document.querySelectorAll('.show-all-button');
        showAllButtons.forEach(button => {
            // Ensure it's properly centered
            button.style.display = 'block';
            button.style.margin = '0 auto';
            console.log("Centered Show All button:", button);
        });
        
        console.log("Search field cleanup complete");
    }
    
    // Run immediately if document is already loaded
    if (document.readyState === 'complete' || document.readyState === 'interactive') {
        removeSearchFields();
    } else {
        // Otherwise, wait for the DOM to be ready
        document.addEventListener('DOMContentLoaded', removeSearchFields);
    }
    
    // Also run after a short delay to catch dynamically added elements
    setTimeout(removeSearchFields, 1000);
})();
