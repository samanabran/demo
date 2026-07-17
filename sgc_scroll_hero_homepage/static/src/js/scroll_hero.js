/** @odoo-module **/

// Scroll Story Hero — cinematic scroll-triggered image-sequence hero.
// Plain vanilla JS, matching the rest of this site's frontend code style
// (see sgc_offplan_rental_property_management's property_search.js /
// property_carousel.js) rather than publicWidget or the Interaction class.
//
// NOTE on the readiness check below (deliberately NOT a bare
// `document.addEventListener('DOMContentLoaded', ...)`  like those files
// use): Odoo 19 ships every module's `web.assets_frontend` JS inside a
// lazily-loaded bundle that only starts executing after the `window.load`
// event (see web/static/src/legacy/js/public/lazyloader.js). By then
// `DOMContentLoaded` has already fired, so a plain listener for it here
// would never run — this hero would stay black forever. Checking
// `document.readyState` first makes init work correctly regardless of
// when this file actually executes.

function sgcInitScrollHeroSections() {

    var EAGER_FRAME_COUNT = 10;

    function whenGsapReady(cb) {
        if (window.gsap && window.ScrollTrigger) {
            cb();
            return;
        }
        document.addEventListener('sgc:gsap-ready', function onReady() {
            document.removeEventListener('sgc:gsap-ready', onReady);
            cb();
        });
    }

    function frameUrl(section, index) {
        var digits = parseInt(section.dataset.frameDigits, 10) || 4;
        var padded = String(index).padStart(digits, '0');
        return (section.dataset.frameBase || '') + padded + (section.dataset.frameExt || '.jpg');
    }

    function resizeCanvas(canvas) {
        var ratio = window.devicePixelRatio || 1;
        canvas.width = canvas.clientWidth * ratio;
        canvas.height = canvas.clientHeight * ratio;
    }

    function drawImage(canvas, ctx, img) {
        if (!ctx || !img || !img.complete || !img.naturalWidth) {
            return;
        }
        var cw = canvas.width;
        var ch = canvas.height;
        var imgRatio = img.naturalWidth / img.naturalHeight;
        var canvasRatio = cw / ch;
        var dw, dh, dx, dy;
        if (imgRatio > canvasRatio) {
            dh = ch;
            dw = ch * imgRatio;
            dx = (cw - dw) / 2;
            dy = 0;
        } else {
            dw = cw;
            dh = cw / imgRatio;
            dx = 0;
            dy = (ch - dh) / 2;
        }
        ctx.clearRect(0, 0, cw, ch);
        ctx.drawImage(img, dx, dy, dw, dh);
    }

    function showStaticFallback(section, frameCount) {
        // prefers-reduced-motion (or missing canvas/frame data): skip the
        // animation entirely, show only the final frame as a plain
        // background, and reveal the search bar immediately.
        section.style.height = '100vh';
        section.classList.add('o_re_scroll_hero--static');

        var canvas = section.querySelector('.o_re_scroll_hero__canvas');
        var ctx = canvas ? canvas.getContext('2d') : null;
        if (canvas && ctx && frameCount) {
            resizeCanvas(canvas);
            var img = new Image();
            img.onload = function () {
                resizeCanvas(canvas);
                drawImage(canvas, ctx, img);
            };
            img.src = frameUrl(section, frameCount);
        }

        var loader = section.querySelector('.o_re_scroll_hero__loader');
        if (loader) {
            loader.style.display = 'none';
        }
        section.querySelectorAll('.o_re_scroll_hero__caption').forEach(function (caption) {
            caption.style.opacity = '0';
        });
        var searchEl = section.querySelector('.o_re_scroll_hero__search');
        if (searchEl) {
            searchEl.style.opacity = '1';
            searchEl.style.pointerEvents = 'auto';
        }
        var hint = section.querySelector('.o_re_scroll_hero__scrollhint');
        if (hint) {
            hint.style.display = 'none';
        }
    }

    function initScrollHero(section) {
        if (section.__sgcScrollHeroInitialized) {
            return;
        }
        section.__sgcScrollHeroInitialized = true;

        var frameCount = parseInt(section.dataset.frameCount, 10) || 0;
        var pinHeight = parseFloat(section.dataset.pinHeight) || 450;
        var pinEl = section.querySelector('.o_re_scroll_hero__pin');
        var canvas = section.querySelector('.o_re_scroll_hero__canvas');
        var ctx = canvas ? canvas.getContext('2d') : null;
        var loaderEl = section.querySelector('.o_re_scroll_hero__loader');
        var captions = section.querySelectorAll('.o_re_scroll_hero__caption');
        var searchEl = section.querySelector('.o_re_scroll_hero__search');
        var scrollHint = section.querySelector('.o_re_scroll_hero__scrollhint');

        var prefersReducedMotion = window.matchMedia &&
            window.matchMedia('(prefers-reduced-motion: reduce)').matches;

        if (prefersReducedMotion || !frameCount || !canvas || !pinEl) {
            showStaticFallback(section, frameCount);
            return;
        }

        // Height read from data-pin-height, not hardcoded — editing that
        // attribute (e.g. via the snippet's XML) is enough to change how
        // long the pinned scroll story lasts, no JS edits needed.
        section.style.height = pinHeight + 'vh';

        var images = new Array(frameCount);
        var loadedCount = 0;

        function markLoaded() {
            loadedCount++;
            if (loaderEl) {
                var pct = Math.round((loadedCount / frameCount) * 100);
                if (pct >= 100) {
                    loaderEl.style.display = 'none';
                } else {
                    loaderEl.textContent = 'Loading ' + pct + '%';
                }
            }
        }

        function loadFrame(zeroBasedIndex, eager) {
            var img = new Image();
            img.loading = eager ? 'eager' : 'lazy';
            img.onload = markLoaded;
            img.onerror = markLoaded;
            img.src = frameUrl(section, zeroBasedIndex + 1);
            images[zeroBasedIndex] = img;
        }

        var eagerCount = Math.min(EAGER_FRAME_COUNT, frameCount);
        for (var i = 0; i < eagerCount; i++) {
            loadFrame(i, true);
        }

        function loadRemainingFrames() {
            for (var j = eagerCount; j < frameCount; j++) {
                loadFrame(j, false);
            }
        }
        if ('requestIdleCallback' in window) {
            window.requestIdleCallback(loadRemainingFrames);
        } else {
            window.setTimeout(loadRemainingFrames, 200);
        }

        resizeCanvas(canvas);
        var onResize = function () {
            resizeCanvas(canvas);
            var img = images[currentFrame];
            if (img) {
                drawImage(canvas, ctx, img);
            }
        };
        window.addEventListener('resize', onResize);

        // requestAnimationFrame-throttled draw: ScrollTrigger's onUpdate can
        // fire many times per scroll tick, but we only ever want to draw
        // once per animation frame.
        var currentFrame = -1;
        var pendingFrame = 0;
        var rafScheduled = false;

        function scheduleDraw(index) {
            pendingFrame = index;
            if (rafScheduled) {
                return;
            }
            rafScheduled = true;
            window.requestAnimationFrame(function () {
                rafScheduled = false;
                if (pendingFrame === currentFrame) {
                    return;
                }
                currentFrame = pendingFrame;
                var img = images[currentFrame];
                if (!img) {
                    return;
                }
                if (img.complete && img.naturalWidth) {
                    drawImage(canvas, ctx, img);
                } else {
                    img.onload = function () {
                        drawImage(canvas, ctx, img);
                    };
                }
            });
        }

        whenGsapReady(function () {
            var gsap = window.gsap;
            var ScrollTrigger = window.ScrollTrigger;
            gsap.registerPlugin(ScrollTrigger);

            // Guard against duplicate ScrollTrigger instances stacking up
            // if the Website Builder re-renders/re-enters edit mode on
            // this same section without a full page reload.
            if (section.__sgcScrollTrigger) {
                section.__sgcScrollTrigger.kill();
            }
            if (section.__sgcTimeline) {
                section.__sgcTimeline.kill();
            }

            var tl = gsap.timeline({ paused: true });

            captions.forEach(function (caption) {
                var start = parseFloat(caption.dataset.progressStart) || 0;
                var end = parseFloat(caption.dataset.progressEnd) || 0;
                var mid = start + (end - start) / 2;
                gsap.set(caption, { opacity: 0 });
                tl.to(caption, { opacity: 1, duration: Math.max(mid - start, 0.001) }, start)
                  .to(caption, { opacity: 0, duration: Math.max(end - mid, 0.001) }, mid);
            });

            if (searchEl) {
                var searchStart = parseFloat(searchEl.dataset.progressStart) || 0.92;
                var searchEnd = parseFloat(searchEl.dataset.progressEnd) || 1.0;
                gsap.set(searchEl, { opacity: 0 });
                searchEl.style.pointerEvents = 'none';
                // Fades in and holds — no matching fade-out tween, so it
                // stays visible once the user has scrolled past searchEnd.
                tl.to(searchEl, {
                    opacity: 1,
                    duration: Math.max(searchEnd - searchStart, 0.001),
                    onStart: function () {
                        searchEl.style.pointerEvents = 'auto';
                    },
                }, searchStart);
            }

            var scrollTrigger = ScrollTrigger.create({
                trigger: section,
                start: 'top top',
                end: 'bottom bottom',
                pin: pinEl,
                scrub: 0.5,
                onUpdate: function (self) {
                    tl.progress(self.progress);
                    var idx = Math.round(self.progress * (frameCount - 1));
                    scheduleDraw(Math.min(frameCount - 1, Math.max(0, idx)));
                    if (scrollHint && self.progress > 0.001) {
                        scrollHint.classList.add('o_re_scroll_hero__scrollhint--hidden');
                    }
                },
            });

            section.__sgcScrollTrigger = scrollTrigger;
            section.__sgcTimeline = tl;
            section.__sgcOnResize = onResize;

            var firstFrame = images[0];
            if (firstFrame) {
                if (firstFrame.complete) {
                    drawImage(canvas, ctx, firstFrame);
                } else {
                    firstFrame.onload = function () {
                        drawImage(canvas, ctx, firstFrame);
                    };
                }
            }
        });
    }

    function teardownScrollHero(section) {
        if (section.__sgcScrollTrigger) {
            section.__sgcScrollTrigger.kill();
        }
        if (section.__sgcTimeline) {
            section.__sgcTimeline.kill();
        }
        if (section.__sgcOnResize) {
            window.removeEventListener('resize', section.__sgcOnResize);
        }
        section.__sgcScrollHeroInitialized = false;
        section.__sgcScrollTrigger = null;
        section.__sgcTimeline = null;
        section.__sgcOnResize = null;
    }

    function scanAndInit(root) {
        (root || document).querySelectorAll('.o_re_scroll_hero').forEach(initScrollHero);
    }

    scanAndInit(document);

    // The Website Builder can drop a new copy of this snippet onto the page
    // (or remove one) without a full reload. A MutationObserver keeps that
    // working under plain vanilla JS, without pulling in the
    // publicWidget/Interaction machinery this codebase otherwise avoids.
    if ('MutationObserver' in window) {
        var observer = new MutationObserver(function (mutations) {
            mutations.forEach(function (mutation) {
                mutation.addedNodes.forEach(function (node) {
                    if (!(node instanceof Element)) {
                        return;
                    }
                    if (node.matches && node.matches('.o_re_scroll_hero')) {
                        initScrollHero(node);
                    }
                    node.querySelectorAll && node.querySelectorAll('.o_re_scroll_hero').forEach(initScrollHero);
                });
                mutation.removedNodes.forEach(function (node) {
                    if (!(node instanceof Element)) {
                        return;
                    }
                    if (node.matches && node.matches('.o_re_scroll_hero')) {
                        teardownScrollHero(node);
                    }
                    node.querySelectorAll && node.querySelectorAll('.o_re_scroll_hero').forEach(teardownScrollHero);
                });
            });
        });
        observer.observe(document.body, { childList: true, subtree: true });
    }
}

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', sgcInitScrollHeroSections);
} else {
    // DOM is already parsed (always true by the time this lazy-loaded
    // bundle runs) — just run now instead of waiting for an event that
    // already fired.
    sgcInitScrollHeroSections();
}
