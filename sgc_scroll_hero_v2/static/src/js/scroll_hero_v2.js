function sgcInitScrollHeroV2() {
    var sections = document.querySelectorAll('section[data-snippet="s_re_scroll_hero_v2"]');
    if (!sections.length) {
        return;
    }

    var instances = new WeakMap();

    var storyBeats = [
        { text: "You\u2019ve imagined this home more times than you can remember.", start: 0.00, end: 0.09 },
        { text: "A place where mornings feel peaceful and evenings feel complete.", start: 0.10, end: 0.19 },
        { text: "Every room holds a piece of who you are.", start: 0.20, end: 0.29 },
        { text: "A place where your family grows and your dreams grow with them.", start: 0.30, end: 0.39 },
        { text: "Laughter fills the silence and love leaves its mark.", start: 0.40, end: 0.49 },
        { text: "The right home doesn\u2019t just shelter you \u2014 it shapes your future.", start: 0.50, end: 0.59 },
        { text: "One decision can turn everything you\u2019ve dreamed into everything you live.", start: 0.60, end: 0.69 },
        { text: "True luxury isn\u2019t measured in space \u2014 it\u2019s measured in how it makes you feel.", start: 0.70, end: 0.79 },
        { text: "Someday, you\u2019ll look around and remember the decision that brought you here.", start: 0.80, end: 0.88 },
        { text: "Your story has been waiting for a place like this.", start: 0.89, end: 1.00, isFinal: true }
    ];

    function pad4(n) {
        return String(n).padStart(4, '0');
    }

    function initHero(section) {
        var frameCount = parseInt(section.dataset.frameCount, 10) || 220;
        var pinHeightVh = parseInt(section.dataset.pinHeight, 10) || 600;
        section.style.setProperty('--sgc-pin-height-v2', pinHeightVh + 'vh');

        // frame_0001..~0010 are an intentional near-black "fade up from
        // night" opening in the source photography, but frame 1 is also
        // what a visitor sees at rest (scroll progress 0) the instant they
        // land - before they've scrolled at all. That made the hero look
        // broken/empty on arrival instead of cinematic. Retiring those
        // darkest frames from the scroll-scrubbable range (below) fixes it
        // for every visitor regardless of how they arrive (fresh load, back
        // button, deep link mid-scroll) since it changes what progress=0
        // *means*, rather than depending on a load-time animation race.
        var INTRO_HOLD_FRAME = Math.min(12, frameCount);

        var canvas = section.querySelector('.s_re_hero_canvas_v2');
        var ctx = canvas.getContext('2d');
        var caption = section.querySelector('.s_re_hero_caption_v2');
        var overlay = section.querySelector('.s_re_hero_overlay_final_v2');
        // Homepage variant transplants sgc_scroll_hero_homepage's search-bar
        // markup, which carries the un-namespaced .s_re_hero_search_wrap
        // class (so scroll_hero.css's pill-search rules apply cleanly,
        // without colliding with this module's own .s_re_hero_search_wrap_v2
        // sizing rules at equal CSS specificity).
        var searchWrap = section.querySelector('.s_re_hero_search_wrap_v2, .s_re_hero_search_wrap');
        var revealDivider = section.querySelector('.s_re_hero_reveal_divider');
        var hint = section.querySelector('.s_re_hero_scroll_hint_v2');
        var loading = section.querySelector('.s_re_hero_loading_v2');

        // Budget select posts a single "min-max" value; split it into the
        // two plain query params /offplan/properties already understands
        // (min_price/max_price) rather than teaching the controller a new
        // param.
        var budgetSelect = section.querySelector('.s_re_hero_search_budget');
        var minPriceInput = section.querySelector('input[name="min_price"]');
        var maxPriceInput = section.querySelector('input[name="max_price"]');
        if (budgetSelect && minPriceInput && maxPriceInput) {
            budgetSelect.addEventListener('change', function () {
                var parts = budgetSelect.value ? budgetSelect.value.split('-') : [];
                minPriceInput.value = parts[0] || '';
                maxPriceInput.value = parts.length > 1 ? (parts[1] || '') : '';
            });
        }

        var reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
        var frameImgs = new Array(frameCount + 1);
        var currentFrame = INTRO_HOLD_FRAME;
        var lastDrawnFrame = -1;
        var activeBeatIndex = -1;
        var engineStarted = false;

        var targetProgress = 0;
        var smoothedProgress = 0;
        var SGC_SMOOTHING = 0.10;
        var loopRunning = false;
        var stillFrames = 0;
        var STILLNESS_THRESHOLD = 0.0005;
        var STILLNESS_FRAMES_REQUIRED = 2;
        var hqSettleToken = 0;

        // --- Audio: Web Audio API buffer engine (not <audio> elements).
        // Both tracks decode once and loop via AudioBufferSourceNode's
        // native looping, which is sample-accurate - unlike <audio>.loop on
        // an MP3, which re-parses the container at each loop boundary and
        // audibly clicks on the encoder's priming/padding samples. That was
        // the real source of the reported "big gaps": ambient_loop.mp3 is
        // only 4s long, so at <audio>.loop it clicked roughly every 4s.
        // Scrub-track speed (never position) is modulated continuously by
        // scroll progress per the original design (0.5x-2.0x) - seeking is
        // what caused the earlier hiccups, so playback never seeks.
        // Crossfades use GainNode automation (linearRampToValueAtTime),
        // which is sample-accurate and self-cancelling (no stacked-tween
        // risk from rapid scroll start/stop). A slow stereo-pan drift on the
        // ambient bed adds a subtle sense of spatial depth.
        var AUDIO_BASE = '/sgc_scroll_hero_v2/static/src/audio/';
        var audioCtx = null;
        var scrubGain = null;
        var ambientGain = null;
        var ambientPanner = null;
        var scrubSource = null;
        var audioReady = false;
        var audioUnlocked = false;
        var panRafId = null;

        function startPanDrift() {
            if (!ambientPanner || panRafId) {
                return;
            }
            var PAN_PERIOD_MS = 11000;
            var PAN_AMOUNT = 0.28;
            (function tick(ts) {
                ambientPanner.pan.value = Math.sin((ts / PAN_PERIOD_MS) * Math.PI * 2) * PAN_AMOUNT;
                panRafId = requestAnimationFrame(tick);
            })(0);
        }

        function initAudio() {
            var Ctx = window.AudioContext || window.webkitAudioContext;
            if (!Ctx) {
                return;
            }
            audioCtx = new Ctx();
            var masterGain = audioCtx.createGain();
            masterGain.connect(audioCtx.destination);

            scrubGain = audioCtx.createGain();
            scrubGain.gain.value = 0;
            scrubGain.connect(masterGain);

            ambientGain = audioCtx.createGain();
            ambientGain.gain.value = 0;
            if (audioCtx.createStereoPanner) {
                ambientPanner = audioCtx.createStereoPanner();
                ambientGain.connect(ambientPanner);
                ambientPanner.connect(masterGain);
            } else {
                ambientGain.connect(masterGain);
            }

            Promise.all([
                fetch(AUDIO_BASE + 'scrub_track.mp3').then(function (r) { return r.arrayBuffer(); }),
                fetch(AUDIO_BASE + 'ambient_loop.mp3').then(function (r) { return r.arrayBuffer(); })
            ]).then(function (raw) {
                return Promise.all([
                    audioCtx.decodeAudioData(raw[0]),
                    audioCtx.decodeAudioData(raw[1])
                ]);
            }).then(function (decoded) {
                scrubSource = audioCtx.createBufferSource();
                scrubSource.buffer = decoded[0];
                scrubSource.loop = true;
                scrubSource.connect(scrubGain);
                scrubSource.start(0);

                var ambientSource = audioCtx.createBufferSource();
                ambientSource.buffer = decoded[1];
                ambientSource.loop = true;
                ambientSource.connect(ambientGain);
                ambientSource.start(0);

                audioReady = true;
                startPanDrift();
            }).catch(function () {
                // Fetch/decode failure just leaves audio silent; the visual
                // engine is entirely independent of this.
            });
        }

        function unlockAudio() {
            if (audioUnlocked || !audioCtx) {
                return;
            }
            audioUnlocked = true;
            if (audioCtx.state === 'suspended') {
                audioCtx.resume().catch(function () {});
            }
        }

        function rampGain(node, target, duration) {
            if (!audioReady) {
                return;
            }
            var now = audioCtx.currentTime;
            node.gain.cancelScheduledValues(now);
            node.gain.setValueAtTime(node.gain.value, now);
            node.gain.linearRampToValueAtTime(target, now + duration);
        }

        var SCRUB_RATE_MIN = 0.5;
        var SCRUB_RATE_MAX = 2.0;
        function updateScrubRate(progress) {
            if (!audioReady) {
                return;
            }
            var rate = SCRUB_RATE_MIN + progress * (SCRUB_RATE_MAX - SCRUB_RATE_MIN);
            scrubSource.playbackRate.value = rate;
        }

        function crossfadeToAmbient() {
            rampGain(scrubGain, 0, 0.6);
            rampGain(ambientGain, 0.6, 0.8);
        }

        function crossfadeToScrub() {
            rampGain(ambientGain, 0, 0.4);
            rampGain(scrubGain, 0.85, 0.4);
        }

        initAudio();

        function frameSrc(i) {
            return '/sgc_scroll_hero_v2/static/src/img/frames/frame_' + pad4(i) + '.webp';
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

        function ensureFrame(i) {
            var img = frameImgs[i];
            if (img) {
                // Already requested (eager preload or the lazy-loader queue),
                // but drawFrame() found it not ready yet. The lazy-loader's
                // own onload only increments its counter - it never repaints
                // - so without this listener a frame whose scroll target was
                // hit before its image finished downloading would never get
                // drawn, even after it loads moments later. addEventListener
                // (not overwriting onload) so the lazy-loader's counter still
                // fires too.
                if (!img.complete || !img.naturalWidth) {
                    img.addEventListener('load', function onFrameLoad() {
                        img.removeEventListener('load', onFrameLoad);
                        if (currentFrame === i) {
                            drawFrame(i);
                        }
                    });
                }
                return;
            }
            img = new Image();
            img.onload = function () {
                if (currentFrame === i) {
                    drawFrame(i);
                }
            };
            img.src = frameSrc(i);
            frameImgs[i] = img;
        }

        function drawFrame(i) {
            var img = frameImgs[i];
            if (!img || !img.complete || !img.naturalWidth) {
                // Sequential preload hasn't reached this frame yet (slow
                // connection, or the user scrolled faster than the lazy
                // loader) - fetch it directly so the sequence catches up
                // instead of freezing on the last successfully drawn frame.
                ensureFrame(i);
                return;
            }
            var cw = canvas.width;
            var ch = canvas.height;
            var c = coverCrop(img, cw, ch);
            ctx.clearRect(0, 0, cw, ch);
            ctx.drawImage(img, c.sx, c.sy, c.sw, c.sh, 0, 0, cw, ch);
        }

        function drawFrameSettled(i) {
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
            var dpr = Math.min(window.devicePixelRatio || 1, 1.5);
            canvas.width = canvas.clientWidth * dpr;
            canvas.height = canvas.clientHeight * dpr;
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
                    // Draw the resting frame (INTRO_HOLD_FRAME, not frame 1)
                    // the INSTANT its image loads, so the canvas never sits
                    // on a stale/blank frame behind the caption.
                    if (i === INTRO_HOLD_FRAME && frameImgs[i] && frameImgs[i].complete) {
                        drawFrame(i);
                    }
                    if (loaded >= eagerCount) {
                        if (loading) {
                            loading.classList.add('s_re_hero_loading_v2_done');
                        }
                        if (!engineStarted) {
                            engineStarted = true;
                            startEngine();
                        }
                        drawFrame(INTRO_HOLD_FRAME);
                    }
                });
            });

            // Batched via setTimeout, not requestIdleCallback: idle callbacks
            // are network fetches in disguise here (~100-200KB/frame, not
            // cheap decode work), and Chrome starves requestIdleCallback
            // hard the moment a tab is backgrounded/hidden - confirmed via
            // live testing, lazy loading stalled completely and permanently
            // partway through as soon as document.hidden became true, well
            // before any "long background" throttling threshold. A visitor
            // who opens the page in a background tab (or switches away
            // while it loads) would otherwise get a permanently incomplete
            // frame sequence with no error, since drawFrame() silently skips
            // whenever frameImgs[i] isn't loaded yet. setTimeout isn't gated
            // by main-thread idle time and only gets throttled after
            // extended backgrounding, so it reliably finishes instead.
            var LAZY_BATCH_SIZE = 8;
            var next = eagerHead + 1;
            function lazyStep() {
                if (next > frameCount) {
                    return;
                }
                for (var n = 0; n < LAZY_BATCH_SIZE && next <= frameCount; n++) {
                    var i = next++;
                    if (!frameImgs[i]) {
                        loadOne(i);
                    }
                }
                setTimeout(lazyStep, 16);
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
                    duration: 0.70,
                    ease: 'power2.in'
                });
            }
        }

        function animateCaptionIn(beat) {
            caption.textContent = beat.text;
            gsap.fromTo(
                caption,
                { opacity: 0, y: 44, scale: 0.94, filter: 'blur(10px)' },
                { opacity: 1, y: 0, scale: 1, filter: 'blur(0px)', duration: 1.1, ease: 'power4.out' }
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
            if (revealDivider) {
                gsap.set(revealDivider, { opacity: t });
            }
            if (t > 0 && hint) {
                gsap.set(hint, { opacity: 0 });
            }
            // Some search-bar markup (e.g. the transplanted V1 pill form used
            // on the homepage variant) ships with tabindex="-1" so a keyboard
            // user can't tab into a form that's still invisible; restore
            // natural tab order once the reveal starts. No-op if the search
            // form has no such attributes (the plain V2 test-page form).
            if (t >= 0.2) {
                markSearchReady();
            }
        }

        function markSearchReady() {
            if (!searchWrap || searchWrap.classList.contains('ready')) {
                return;
            }
            searchWrap.classList.add('ready');
            searchWrap.querySelectorAll('[tabindex="-1"]').forEach(function (el) {
                el.removeAttribute('tabindex');
            });
        }

        // The tail of the frame sequence (~frame 210-220) fades the aerial
        // shot down to near-black night, which read as the hero "going
        // dark" right as the search bar finishes revealing. Frame scrubbing
        // freezes at FRAME_FREEZE_PROGRESS (frame ~205, still bright golden-
        // hour daylight) so the backdrop holds on the aerial view; the
        // caption/overlay/search-bar reveal keeps using the real, unclamped
        // progress so the final beat still animates and completes normally.
        var FRAME_FREEZE_PROGRESS = 0.93;

        function freezeFrameIndex() {
            return Math.min(frameCount, Math.max(1, Math.round(FRAME_FREEZE_PROGRESS * (frameCount - 1)) + 1));
        }

        function applyProgress(progress) {
            updateCaption(progress);
            updateFinalReveal(progress);
            updateScrubRate(progress);
            var frameProgress = Math.min(progress, FRAME_FREEZE_PROGRESS);
            // Map scroll progress across [INTRO_HOLD_FRAME .. frameCount]
            // instead of [1 .. frameCount], so progress=0 (page landing,
            // before any scroll) always resolves to the first well-lit
            // frame rather than the near-black frame 1.
            var idx = Math.round(INTRO_HOLD_FRAME + frameProgress * (frameCount - INTRO_HOLD_FRAME));
            idx = Math.min(frameCount, Math.max(INTRO_HOLD_FRAME, idx));
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
            crossfadeToScrub();
            function tick() {
                smoothedProgress += (targetProgress - smoothedProgress) * SGC_SMOOTHING;
                var delta = Math.abs(targetProgress - smoothedProgress);
                stillFrames = delta < STILLNESS_THRESHOLD ? stillFrames + 1 : 0;

                if (stillFrames >= STILLNESS_FRAMES_REQUIRED) {
                    smoothedProgress = targetProgress;
                    applyProgress(smoothedProgress);
                    drawFrameSettled(currentFrame);
                    loopRunning = false;
                    crossfadeToAmbient();
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
                unlockAudio();
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
                drawFrame(freezeFrameIndex());
                drawFrameSettled(freezeFrameIndex());
                gsap && gsap.set ? gsap.set(overlay, { opacity: 1 }) : (overlay.style.opacity = 1);
                if (searchWrap) {
                    searchWrap.style.opacity = 1;
                    searchWrap.style.pointerEvents = 'auto';
                }
                if (revealDivider) {
                    revealDivider.style.opacity = 1;
                }
                markSearchReady();
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
    document.addEventListener('DOMContentLoaded', sgcInitScrollHeroV2);
} else {
    sgcInitScrollHeroV2();
}
