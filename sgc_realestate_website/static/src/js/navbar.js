/**
 * SGC TECH AI Real Estate - Navbar Mobile Toggle
 * Handles mobile menu collapse/expand functionality
 */

document.addEventListener('DOMContentLoaded', function() {
    // Get navbar toggler and collapse elements
    const navbarToggler = document.querySelector('.navbar-toggler');
    const navbarCollapse = document.querySelector('.navbar-collapse');
    
    if (navbarToggler && navbarCollapse) {
        // Toggle menu on button click
        navbarToggler.addEventListener('click', function() {
            navbarCollapse.classList.toggle('show');
        });
        
        // Close menu when clicking on a nav link
        const navLinks = document.querySelectorAll('.nav-link');
        navLinks.forEach(link => {
            link.addEventListener('click', function() {
                navbarCollapse.classList.remove('show');
            });
        });
        
        // Close menu when clicking outside
        document.addEventListener('click', function(event) {
            const isClickInside = navbarToggler.contains(event.target) || 
                                  navbarCollapse.contains(event.target);
            if (!isClickInside) {
                navbarCollapse.classList.remove('show');
            }
        });
    }
});
