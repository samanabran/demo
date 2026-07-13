// Property Filtering Functionality
(function() {
    'use strict';

    document.addEventListener('DOMContentLoaded', function() {
        const countryFilter = document.getElementById('filter-country');
        const typeFilter = document.getElementById('filter-type');
        const priceFilter = document.getElementById('filter-price');
        const propertyCards = document.querySelectorAll('.property-card');

        // Add event listeners
        [countryFilter, typeFilter, priceFilter].forEach(filter => {
            if (filter) {
                filter.addEventListener('change', applyFilters);
            }
        });

        function applyFilters() {
            const selectedCountry = countryFilter ? countryFilter.value : '';
            const selectedType = typeFilter ? typeFilter.value : '';
            const selectedPrice = priceFilter ? priceFilter.value : '';

            let visibleCount = 0;

            propertyCards.forEach(card => {
                let matchCountry = true;
                let matchType = true;
                let matchPrice = true;

                // Check country filter
                if (selectedCountry) {
                    const cardCountry = card.dataset.country;
                    matchCountry = cardCountry === selectedCountry;
                }

                // Check type filter
                if (selectedType) {
                    const cardType = card.dataset.type;
                    matchType = cardType === selectedType;
                }

                // Check price filter
                if (selectedPrice) {
                    const cardPrice = parseInt(card.dataset.price);
                    const [minPrice, maxPrice] = selectedPrice.split('-').map(p => parseInt(p));
                    matchPrice = cardPrice >= minPrice && (maxPrice ? cardPrice <= maxPrice : true);
                }

                if (matchCountry && matchType && matchPrice) {
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
            let noResults = document.getElementById('filter-no-results');
            const grid = document.querySelector('.property-grid');
            
            if (!grid) return;

            if (show && !noResults) {
                noResults = document.createElement('div');
                noResults.id = 'filter-no-results';
                noResults.className = 'alert alert-info text-center mt-4';
                noResults.textContent = 'No properties match your filters. Try adjusting your criteria.';
                grid.parentElement.appendChild(noResults);
            } else if (!show && noResults) {
                noResults.remove();
            }
        }
    });
})();
