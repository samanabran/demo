function sgcInitScrollHeroV2() {
    var sections = document.querySelectorAll('section[data-snippet="s_re_scroll_hero_v2"]');
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
        var frameCount = parseInt(section.dataset.frameCount, 10) || 224;
        var pinHeightVh = parseInt(section.dataset.pinHeight, 10) || 600;
        section.style.setProperty('--sgc-pin-height-v2', pinHeightVh + 'vh');

        var canvas = section.querySelector('.s_re_hero_canvas_v2');
        var ctx = canvas.getContext('2d');
        var caption = section.querySelector('.s_re_hero_caption_v2');
        var overlay = section.querySelector('.s_re_hero_overlay_final_v2');
        var searchWrap = section.querySelector('.s_re_hero_search_wrap_v2');
        var hint = section.querySelector('.s_re_hero_scroll_hint_v2');
        var loading = section.querySelector('.s_re_hero_loading_v2');

        var reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
        var frameImgs = new Array(frameCount + 1);
        var currentFrame = 1;
        var lastDrawnFrame = -1;
        var activeBeatIndex = -1;
        var engineStarted = false;

        var targetProgress = 0;
        var smoothedProgress = 0;
        var SGC_SMOOTHING = 0.15;
        var loopRunning = false;
        var stillFrames = 0;
        var STILLNESS_THRESHOLD = 0.0005;
        var STILLNESS_FRAMES_REQUIRED = 2;
        var hqSettleToken = 0;

        // --- Audio: scrub the real soundtrack while actively scrolling,
        // crossfade into a looping ambient bed once scrolling settles. Both
        // elements play continuously (muted) from load so the crossfade is
        // just a volume tween, never a play()/pause() race. Nothing is
        // audible until the user's first scroll/touch/wheel, per browser
        // autoplay policy -- there is no way to play audible sound before
        // that gesture, muted playback is the only thing allowed pre-gesture.
        var AUDIO_BASE = '/sgc_scroll_hero_v2/static/src/audio/';
        var scrubAudio = new Audio(AUDIO_BASE + 'scrub_track.mp3');
        var ambientAudio = new Audio(AUDIO_BASE + 'ambient_loop.mp3');
        scrubAudio.preload = 'auto';
        scrubAudio.muted = true;
        scrubAudio.volume = 0.85;
        ambientAudio.preload = 'auto';
        ambientAudio.muted = true;
        ambientAudio.loop = true;
        ambientAudio.volume = 0;
        var audioUnlocked = false;
        var scrubAudioReady = false;
        scrubAudio.addEventListener('loadedmetadata', function () {
            scrubAudioReady = true;
        });
        scrubAudio.play().catch(function () {});
        ambientAudio.play().catch(function () {});

        function unlockAudio() {
            if (audioUnlocked) {
                return;
            }
            audioUnlocked = true;
            scrubAudio.muted = false;
            ambientAudio.muted = false;
            scrubAudio.play().catch(function () {});
            ambientAudio.play().catch(function () {});
        }

        function scrubToProgress(progress) {
            if (!scrubAudioReady || !scrubAudio.duration) {
                return;
            }
            var targetTime = progress * scrubAudio.duration;
            if (Math.abs(scrubAudio.currentTime - targetTime) > 0.08) {
                scrubAudio.currentTime = targetTime;
            }
        }

        function crossfadeToAmbient() {
            if (!window.gsap) {
                scrubAudio.volume = 0;
                ambientAudio.volume = 0.6;
                return;
            }
            gsap.to(scrubAudio, { volume: 0, duration: 0.6, ease: 'power1.out' });
            gsap.to(ambientAudio, { volume: 0.6, duration: 0.8, ease: 'power1.in' });
        }

        function crossfadeToScrub() {
            if (!window.gsap) {
                scrubAudio.volume = 0.85;
                ambientAudio.volume = 0;
                return;
            }
            gsap.to(ambientAudio, { volume: 0, duration: 0.4, ease: 'power1.out' });
            gsap.to(scrubAudio, { volume: 0.85, duration: 0.4, ease: 'power1.in' });
        }

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
        }

        function applyProgress(progress) {
            updateCaption(progress);
            updateFinalReveal(progress);
            scrubToProgress(progress);
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
                drawFrame(frameCount);
                drawFrameSettled(frameCount);
                gsap && gsap.set ? gsap.set(overlay, { opacity: 1 }) : (overlay.style.opacity = 1);
                if (searchWrap) {
                    searchWrap.style.opacity = 1;
                    searchWrap.style.pointerEvents = 'auto';
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
    document.addEventListener('DOMContentLoaded', sgcInitScrollHeroV2);
} else {
    sgcInitScrollHeroV2();
}
