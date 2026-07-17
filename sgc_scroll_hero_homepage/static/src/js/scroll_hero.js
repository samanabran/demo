function sgcInitScrollHero() {
    var sections = document.querySelectorAll('section[data-snippet="s_re_scroll_hero"]');
    if (!sections.length) {
        return;
    }

    var instances = new WeakMap();

    var storyBeats = [
        { text: "Before it's an address, it's a feeling.", start: 0.00, end: 0.08 },
        { text: "A place you haven't found yet — but already miss.", start: 0.10, end: 0.18 },
        { text: "Somewhere, a street is waiting to learn your name.", start: 0.20, end: 0.28 },
        { text: "The porch light you'll leave on for the people you love.", start: 0.30, end: 0.38 },
        { text: "A door that will learn the sound of your keys.", start: 0.40, end: 0.48 },
        { text: "Walls that don't know your laughter yet.", start: 0.50, end: 0.58 },
        { text: "A window where morning will find you first.", start: 0.60, end: 0.68 },
        { text: "This is what 'home' means, before it means anything else.", start: 0.70, end: 0.78 },
        { text: "Every homeowner remembers the day it stopped being a house.", start: 0.80, end: 0.88 },
        { text: "Let's find yours.", start: 0.90, end: 1.00, isFinal: true }
    ];

    function pad4(n) {
        return String(n).padStart(4, '0');
    }

    function initHero(section) {
        var frameCount = parseInt(section.dataset.frameCount, 10) || 240;
        var pinHeightVh = parseInt(section.dataset.pinHeight, 10) || 600;
        section.style.setProperty('--sgc-pin-height', pinHeightVh + 'vh');

        var canvas = section.querySelector('.s_re_hero_canvas');
        var ctx = canvas.getContext('2d');
        var caption = section.querySelector('.s_re_hero_caption');
        var overlay = section.querySelector('.s_re_hero_overlay_final');
        var searchWrap = section.querySelector('.s_re_hero_search_wrap');
        var hint = section.querySelector('.s_re_hero_scroll_hint');
        var loading = section.querySelector('.s_re_hero_loading');

        var reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
        var frameImgs = new Array(frameCount + 1);
        var currentFrame = 1;
        var lastDrawnFrame = -1;
        var activeBeatIndex = -1;
        var engineStarted = false;

        // Scroll smoothing: the frame-sequence and the caption/final-reveal
        // timeline both read from this single lerped value so they can never
        // visually desync from each other. targetProgress tracks raw scroll
        // position 1:1; smoothedProgress chases it every animation frame,
        // producing the "catch-up" glide instead of instant frame-snapping.
        var targetProgress = 0;
        var smoothedProgress = 0;
        var SGC_SMOOTHING = 0.15;
        var loopRunning = false;
        var stillFrames = 0;
        var STILLNESS_THRESHOLD = 0.0005;
        var STILLNESS_FRAMES_REQUIRED = 2;
        var hqSettleToken = 0;

        function frameSrc(i) {
            return '/sgc_scroll_hero_homepage/static/src/img/frames/frame_' + pad4(i) + '.webp';
        }

        function coverCrop(img, cw, ch) {
            var iw = img.naturalWidth;
            var ih = img.naturalHeight;
            var canvasRatio = cw / ch;
            var imgRatio = iw / ih;
            var sx, sy, sw, sh;
            if (imgRatio > canvasRatio) {
                sh = ih;
                sw = ih * canvasRatio;
                sx = (iw - sw) / 2;
                sy = 0;
            } else {
                sw = iw;
                sh = iw / canvasRatio;
                sx = 0;
                sy = (ih - sh) / 2;
            }
            return { sx: sx, sy: sy, sw: sw, sh: sh };
        }

        function drawFrame(i) {
            var img = frameImgs[i];
            if (!img || !img.complete || !img.naturalWidth) {
                return;
            }
            var cw = canvas.width;
            var ch = canvas.height;
            var c = coverCrop(img, cw, ch);
            ctx.clearRect(0, 0, cw, ch);
            ctx.drawImage(img, c.sx, c.sy, c.sw, c.sh, 0, 0, cw, ch);
        }

        function drawFrameSettled(i) {
            // Runs once, only once scrolling has actually stopped. Chrome/
            // Firefox's createImageBitmap resizeQuality:'high' resamples
            // measurably better than drawImage's own scaling, so the one
            // frame the user is left looking at gets the best result even
            // though it's too costly (async decode) to run on every tick.
            var img = frameImgs[i];
            if (!img || !img.complete || !img.naturalWidth || !window.createImageBitmap) {
                return;
            }
            var cw = canvas.width;
            var ch = canvas.height;
            var c = coverCrop(img, cw, ch);
            var token = ++hqSettleToken;
            createImageBitmap(img, c.sx, c.sy, c.sw, c.sh, {
                resizeWidth: cw,
                resizeHeight: ch,
                resizeQuality: 'high'
            }).then(function (bitmap) {
                if (token !== hqSettleToken || loopRunning) {
                    bitmap.close();
                    return;
                }
                ctx.clearRect(0, 0, cw, ch);
                ctx.drawImage(bitmap, 0, 0);
                bitmap.close();
            }).catch(function () {});
        }

        function resizeCanvas() {
            // Source frames are 1920x1080. Above ~1.5x that's already more
            // buffer pixels than the frames have real detail for, so the
            // raw devicePixelRatio (2, 2.5, 3 on modern displays) forces an
            // upscale draw that reads soft the moment scrolling stops and
            // the eye has time to inspect a static frame. Clamping trades a
            // little theoretical ceiling on the most extreme displays for
            // never demanding more resolution than the source can give.
            var dpr = Math.min(window.devicePixelRatio || 1, 1.5);
            canvas.width = canvas.clientWidth * dpr;
            canvas.height = canvas.clientHeight * dpr;
            // Setting canvas.width/height resets all 2D context state, so
            // smoothing must be re-applied on every resize, not just once.
            ctx.imageSmoothingEnabled = true;
            ctx.imageSmoothingQuality = 'high';
            drawFrame(currentFrame);
        }

        function setLoadingProgress(pct) {
            if (loading) {
                loading.style.setProperty('--pct', pct + '%');
                loading.setAttribute('data-pct', pct);
            }
        }

        function preload() {
            var eagerHead = Math.min(15, frameCount);
            // The reduced-motion fallback draws frameCount immediately on
            // startup, so it must be part of the eager batch too -- otherwise
            // it can still be unloaded when startEngine() tries to draw it,
            // leaving the hero blank until the lazy queue happens to reach it.
            var eagerList = [];
            for (var i = 1; i <= eagerHead; i++) {
                eagerList.push(i);
            }
            if (eagerList.indexOf(frameCount) === -1) {
                eagerList.push(frameCount);
            }
            var eagerCount = eagerList.length;
            var loaded = 0;

            function loadOne(i, cb) {
                var img = new Image();
                img.onload = img.onerror = function () {
                    loaded++;
                    if (cb) {
                        cb();
                    }
                };
                img.src = frameSrc(i);
                frameImgs[i] = img;
            }

            eagerList.forEach(function (i) {
                loadOne(i, function () {
                    setLoadingProgress(Math.round((loaded / eagerCount) * 100));
                    if (loaded >= eagerCount) {
                        if (loading) {
                            loading.style.display = 'none';
                        }
                        if (!engineStarted) {
                            engineStarted = true;
                            startEngine();
                        }
                        drawFrame(1);
                    }
                });
            });

            var next = eagerHead + 1;
            function lazyStep() {
                if (next > frameCount) {
                    return;
                }
                var i = next++;
                if (!frameImgs[i]) {
                    loadOne(i);
                }
                if (window.requestIdleCallback) {
                    window.requestIdleCallback(lazyStep, { timeout: 500 });
                } else {
                    setTimeout(lazyStep, 16);
                }
            }
            lazyStep();
        }

        function animateCaptionOut(beat) {
            if (beat.isFinal) {
                gsap.to(caption, { scale: 0.92, opacity: 0.3, duration: 0.5, ease: 'power2.in' });
            } else {
                gsap.to(caption, {
                    opacity: 0,
                    y: -34,
                    scale: 0.97,
                    filter: 'blur(6px)',
                    duration: 0.55,
                    ease: 'power2.in'
                });
            }
        }

        function animateCaptionIn(beat) {
            caption.textContent = beat.text;
            gsap.fromTo(
                caption,
                { opacity: 0, y: 44, scale: 0.94, filter: 'blur(10px)' },
                { opacity: 1, y: 0, scale: 1, filter: 'blur(0px)', duration: 0.9, ease: 'power3.out' }
            );
        }

        function updateCaption(progress) {
            var beatIndex = -1;
            for (var i = 0; i < storyBeats.length; i++) {
                if (progress >= storyBeats[i].start && progress <= storyBeats[i].end) {
                    beatIndex = i;
                    break;
                }
            }
            if (beatIndex === activeBeatIndex) {
                return;
            }
            if (activeBeatIndex !== -1) {
                animateCaptionOut(storyBeats[activeBeatIndex]);
            }
            activeBeatIndex = beatIndex;
            if (beatIndex !== -1) {
                animateCaptionIn(storyBeats[beatIndex]);
            }
        }

        function updateFinalReveal(progress) {
            var finalBeat = storyBeats[storyBeats.length - 1];
            var t = (progress - finalBeat.start) / (finalBeat.end - finalBeat.start);
            t = Math.min(1, Math.max(0, t));
            gsap.set(overlay, { opacity: t });
            gsap.set(searchWrap, {
                xPercent: -50,
                yPercent: -50,
                opacity: t,
                scale: 0.9 + 0.1 * t,
                pointerEvents: t > 0.5 ? 'auto' : 'none'
            });
            if (t > 0 && hint) {
                gsap.set(hint, { opacity: 0 });
            }
            // Gate the icon stagger CSS animation: mark ready once the
            // search bar begins its fade-in so the per-icon animation-delay
            // cascade only fires after the form itself is visible (this also
            // restores keyboard tab order — see markSearchReady above).
            if (t >= 0.2) {
                markSearchReady();
            }
        }

        function markSearchReady() {
            // The inputs/select/button ship with tabindex="-1" in markup so a
            // keyboard user tabbing through the page can't land on a form
            // that's still invisible (opacity 0, pointer-events none) for
            // most of the 600vh scroll. Once the reveal actually starts,
            // restore each element's natural tab order.
            if (!searchWrap || searchWrap.classList.contains('ready')) {
                return;
            }
            searchWrap.classList.add('ready');
            searchWrap.querySelectorAll('[tabindex="-1"]').forEach(function (el) {
                el.removeAttribute('tabindex');
            });
        }

        function applyProgress(progress) {
            updateCaption(progress);
            updateFinalReveal(progress);
            var idx = Math.min(frameCount, Math.max(1, Math.round(progress * (frameCount - 1)) + 1));
            currentFrame = idx;
            if (idx !== lastDrawnFrame) {
                drawFrame(idx);
                lastDrawnFrame = idx;
            }
        }

        function startRenderLoop() {
            if (loopRunning) {
                return;
            }
            loopRunning = true;
            stillFrames = 0;
            function tick() {
                smoothedProgress += (targetProgress - smoothedProgress) * SGC_SMOOTHING;
                var delta = Math.abs(targetProgress - smoothedProgress);
                stillFrames = delta < STILLNESS_THRESHOLD ? stillFrames + 1 : 0;

                if (stillFrames >= STILLNESS_FRAMES_REQUIRED) {
                    smoothedProgress = targetProgress;
                    applyProgress(smoothedProgress);
                    drawFrameSettled(currentFrame);
                    loopRunning = false;
                    return; // at rest: stop scheduling further ticks
                }

                applyProgress(smoothedProgress);
                requestAnimationFrame(tick);
            }
            requestAnimationFrame(tick);
        }

        function fadeHintOnFirstInput() {
            var fired = false;
            function fade() {
                if (fired) {
                    return;
                }
                fired = true;
                if (hint) {
                    hint.style.opacity = 0;
                }
            }
            window.addEventListener('wheel', fade, { once: true, passive: true });
            window.addEventListener('touchmove', fade, { once: true, passive: true });
            window.addEventListener('scroll', fade, { once: true, passive: true });
        }

        function setupScrollTrigger() {
            gsap.registerPlugin(ScrollTrigger);

            var existing = instances.get(section);
            if (existing && existing.scrollTrigger) {
                existing.scrollTrigger.kill();
            }

            var st = ScrollTrigger.create({
                trigger: section,
                start: 'top top',
                end: 'bottom bottom',
                scrub: 0.4,
                onUpdate: function (self) {
                    targetProgress = self.progress;
                    startRenderLoop();
                }
            });
            instances.set(section, { scrollTrigger: st });
            startRenderLoop();
        }

        function startEngine() {
            if (reducedMotion) {
                drawFrame(frameCount);
                drawFrameSettled(frameCount);
                gsap && gsap.set ? gsap.set(overlay, { opacity: 1 }) : (overlay.style.opacity = 1);
                if (searchWrap) {
                    searchWrap.style.opacity = 1;
                    searchWrap.style.pointerEvents = 'auto';
                    markSearchReady();
                }
                if (hint) {
                    hint.style.display = 'none';
                }
                caption.textContent = storyBeats[storyBeats.length - 1].text;
                caption.style.opacity = 1;
                return;
            }

            function onGsapReady() {
                document.removeEventListener('sgc:gsap-ready', onGsapReady);
                setupScrollTrigger();
            }

            if (window.gsap && window.ScrollTrigger) {
                setupScrollTrigger();
            } else {
                document.addEventListener('sgc:gsap-ready', onGsapReady);
            }

            fadeHintOnFirstInput();
        }

        window.addEventListener('resize', resizeCanvas);
        resizeCanvas();
        preload();
    }

    sections.forEach(initHero);
}

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', sgcInitScrollHero);
} else {
    sgcInitScrollHero();
}
