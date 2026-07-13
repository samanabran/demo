/** @odoo-module **/

// Assessment Portal JavaScript
document.addEventListener('DOMContentLoaded', function() {
    // Character counter for textareas
    const textareas = document.querySelectorAll('.assessment-answer');
    
    textareas.forEach(function(textarea) {
        const counterId = 'charCount' + textarea.id.replace('q', '');
        const counter = document.getElementById(counterId);
        
        if (counter) {
            textarea.addEventListener('input', function() {
                counter.textContent = this.value.length;
            });
        }
    });

    // Form validation
    const form = document.getElementById('assessmentForm');
    if (form) {
        form.addEventListener('submit', function(e) {
            const textareas = form.querySelectorAll('.assessment-answer');
            let valid = true;
            
            textareas.forEach(function(textarea) {
                if (textarea.value.length < 50) {
                    valid = false;
                    textarea.classList.add('is-invalid');
                } else {
                    textarea.classList.remove('is-invalid');
                }
            });
            
            if (!valid) {
                e.preventDefault();
                alert('Please ensure all answers are at least 50 characters long.');
            }
        });
    }
});
