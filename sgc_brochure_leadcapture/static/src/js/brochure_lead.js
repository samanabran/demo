(function () {
    // Injected client-side rather than via QWeb inherit_id/xpath: this page
    // belongs to sgc_offplan_rental_property_management (not modified by
    // this module), so the button/modal are built and attached here once
    // the real page has rendered, using the property id parsed from the URL.
    //
    // This file loads via web.assets_frontend_lazy, which by design
    // executes AFTER the page has already finished loading -- a
    // DOMContentLoaded listener registered at that point would never fire,
    // since the event already passed. Run immediately if the document is
    // already interactive/complete, matching the pattern already used in
    // sgc_scroll_hero_homepage/static/src/js/scroll_hero.js.
    function initBrochureLead() {
        var match = window.location.pathname.match(/\/offplan\/property\/(\d+)/);
        if (!match) {
            return;
        }
        var propertyId = match[1];
        var anchor = document.querySelector('.property-highlights');
        if (!anchor || document.querySelector('.sgc_brochure_btn')) {
            return;
        }

        var wrap = document.createElement('div');
        wrap.innerHTML =
            '<button type="button" class="btn sgc_brochure_btn mb-4" data-bs-toggle="modal" data-bs-target="#sgc_brochure_modal">' +
            '  <span class="fa fa-file-pdf-o" aria-hidden="true"></span> Download Brochure' +
            '</button>' +
            '<div class="modal fade" id="sgc_brochure_modal" tabindex="-1" aria-hidden="true">' +
            '  <div class="modal-dialog modal-dialog-centered">' +
            '    <div class="modal-content sgc_brochure_modal_content">' +
            '      <div class="modal-header">' +
            '        <h5 class="modal-title">Download Brochure</h5>' +
            '        <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>' +
            '      </div>' +
            '      <div class="modal-body">' +
            '        <p class="text-muted mb-3">Leave your details and the brochure download will start right away.</p>' +
            '        <form class="sgc_brochure_form">' +
            '          <div class="mb-3"><label class="form-label">Name</label><input type="text" class="form-control" name="name" required="required"/></div>' +
            '          <div class="mb-3"><label class="form-label">Email</label><input type="email" class="form-control" name="email" required="required"/></div>' +
            '          <div class="mb-3"><label class="form-label">Phone</label><input type="tel" class="form-control" name="phone" required="required"/></div>' +
            '          <div class="sgc_brochure_form_error text-danger mb-2" style="display:none;"></div>' +
            '          <button type="submit" class="btn sgc_brochure_submit_btn w-100"><span class="sgc_brochure_submit_label">Download Brochure</span></button>' +
            '        </form>' +
            '      </div>' +
            '    </div>' +
            '  </div>' +
            '</div>';

        while (wrap.firstChild) {
            anchor.parentNode.insertBefore(wrap.firstChild, anchor);
        }

        var modal = document.getElementById('sgc_brochure_modal');
        var form = modal.querySelector('.sgc_brochure_form');
        var errorBox = modal.querySelector('.sgc_brochure_form_error');
        var submitBtn = modal.querySelector('.sgc_brochure_submit_btn');
        var submitLabel = modal.querySelector('.sgc_brochure_submit_label');

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
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initBrochureLead);
    } else {
        initBrochureLead();
    }
})();
