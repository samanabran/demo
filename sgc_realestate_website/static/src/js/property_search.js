// Property Search Functionality
(function() {
    'use strict';

    document.addEventListener('DOMContentLoaded', function() {
        const searchInput = document.getElementById('property-search');
        const searchButton = document.getElementById('search-button');
        const propertyCards = document.querySelectorAll('.property-card');

        if (searchButton) {
            searchButton.addEventListener('click', performSearch);
        }

        if (searchInput) {
            searchInput.addEventListener('keypress', function(e) {
                if (e.key === 'Enter') {
                    performSearch();
                }
            });
        }

        function performSearch() {
            const searchQuery = searchInput.value.toLowerCase();
            let visibleCount = 0;

            propertyCards.forEach(card => {
                const titleEl = card.querySelector('.card-title') || card.querySelector('h3') || card.querySelector('h5');
                const locationEl = card.querySelector('.property-location');

                const name = titleEl ? titleEl.textContent.toLowerCase() : '';
                const location = locationEl ? locationEl.textContent.toLowerCase() : '';

                if (name.includes(searchQuery) || location.includes(searchQuery) || searchQuery === '') {
                    card.style.display = 'block';
                    visibleCount++;
                } else {
                    card.style.display = 'none';
                }
            });

            // Show no results message
            updateNoResultsMessage(visibleCount === 0);
        }

        function updateNoResultsMessage(show) {
            let noResults = document.getElementById('no-results-message');
            
            if (show && !noResults) {
                noResults = document.createElement('div');
                noResults.id = 'no-results-message';
                noResults.className = 'alert alert-info text-center';
                noResults.textContent = 'No properties found matching your search.';
                document.querySelector('.property-grid').parentElement.appendChild(noResults);
            } else if (!show && noResults) {
                noResults.remove();
            }
        }
    });
})();
