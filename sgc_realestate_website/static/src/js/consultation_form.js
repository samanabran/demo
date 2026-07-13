// Consultation Form Functionality
(function() {
    'use strict';

    document.addEventListener('DOMContentLoaded', function() {
        const form = document.getElementById('consultation_form');
        
        if (!form) return;

        form.addEventListener('submit', function(e) {
            e.preventDefault();
            handleFormSubmit(form);
        });

        // Add real-time validation
        const inputs = form.querySelectorAll('input[required], select[required]');
        inputs.forEach(input => {
            input.addEventListener('blur', validateField);
            input.addEventListener('change', validateField);
        });
    });

    function validateField(e) {
        const field = e.target;
        const value = field.value.trim();
        const isValid = value.length > 0;

        if (!isValid) {
            field.classList.add('is-invalid');
        } else {
            field.classList.remove('is-invalid');
            
            // Additional validation for email
            if (field.type === 'email') {
                const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
                if (!emailRegex.test(value)) {
                    field.classList.add('is-invalid');
                } else {
                    field.classList.remove('is-invalid');
                }
            }
            
            // Additional validation for phone
            if (field.type === 'tel') {
                const phoneRegex = /^\d{10,}$/;
                const digitsOnly = value.replace(/\D/g, '');
                if (!phoneRegex.test(digitsOnly)) {
                    field.classList.add('is-invalid');
                } else {
                    field.classList.remove('is-invalid');
                }
            }
        }
    }

    function handleFormSubmit(form) {
        // Validate all required fields
        const inputs = form.querySelectorAll('input[required], select[required]');
        let isFormValid = true;

        inputs.forEach(input => {
            if (!input.value.trim()) {
                input.classList.add('is-invalid');
                isFormValid = false;
            }
        });

        if (isFormValid) {
            // Submit form via AJAX
            const formData = new FormData(form);
            
            fetch(form.action, {
                method: 'POST',
                body: formData,
            })
            .then(async response => {
                let data = {};

                try {
                    data = await response.json();
                } catch (err) {
                    showErrorMessage('Unable to submit right now. Please try again.');
                    return;
                }

                if (!response.ok || !data.success) {
                    showErrorMessage(data.message || 'Unable to submit right now. Please try again.');
                    return;
                }

                showSuccessMessage();
                form.reset();
            })
            .catch(error => {
                console.error('Error:', error);
                showErrorMessage('Unable to submit right now. Please try again.');
            });
        }
    }

    function showSuccessMessage() {
        const successMsg = document.getElementById('success_message');
        const form = document.getElementById('consultation_form');
        
        if (successMsg && form) {
            form.style.display = 'none';
            successMsg.style.display = 'block';
            
            // Scroll to message
            successMsg.scrollIntoView({ behavior: 'smooth' });
        }
    }

    function showErrorMessage(message) {
        const errorDiv = document.createElement('div');
        errorDiv.className = 'alert alert-danger alert-dismissible fade show';
        errorDiv.innerHTML = `
            <strong>Error!</strong> ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        const form = document.getElementById('consultation_form');
        form.parentElement.insertBefore(errorDiv, form);
    }
})();
