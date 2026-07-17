(function () {
    document.addEventListener('DOMContentLoaded', function () {
        var modal = document.getElementById('sgc_brochure_modal');
        if (!modal) {
            return;
        }
        var form = modal.querySelector('.sgc_brochure_form');
        var errorBox = modal.querySelector('.sgc_brochure_form_error');
        var submitBtn = modal.querySelector('.sgc_brochure_submit_btn');
        var submitLabel = modal.querySelector('.sgc_brochure_submit_label');
        var triggerBtn = document.querySelector('.sgc_brochure_btn');
        var propertyId = triggerBtn ? triggerBtn.getAttribute('data-property-id') : null;

        function setLoading(loading) {
            submitBtn.disabled = loading;
            submitLabel.textContent = loading ? 'Please wait…' : 'Download Brochure';
        }

        function showError(message) {
            errorBox.textContent = message;
            errorBox.style.display = 'block';
        }

        form.addEventListener('submit', function (ev) {
            ev.preventDefault();
            errorBox.style.display = 'none';
            setLoading(true);

            var payload = {
                property_id: propertyId,
                name: form.querySelector('[name="name"]').value,
                email: form.querySelector('[name="email"]').value,
                phone: form.querySelector('[name="phone"]').value,
            };

            fetch('/brochure/lead/submit', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ jsonrpc: '2.0', method: 'call', params: payload }),
            })
                .then(function (resp) { return resp.json(); })
                .then(function (data) {
                    var result = data.result || {};
                    setLoading(false);
                    if (!result.success) {
                        showError(result.error || 'Something went wrong. Please try again.');
                        return;
                    }
                    window.location.href = result.download_url;
                    var bsModal = window.bootstrap && window.bootstrap.Modal
                        ? window.bootstrap.Modal.getOrCreateInstance(modal)
                        : null;
                    if (bsModal) {
                        bsModal.hide();
                    }
                    form.reset();
                })
                .catch(function () {
                    setLoading(false);
                    showError('Network error. Please try again.');
                });
        });
    });
})();
