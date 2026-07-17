document.addEventListener('DOMContentLoaded', function () {
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
        var activeBeatIndex = -1;
        var rafPending = false;
        var engineStarted = false;

        function frameSrc(i) {
            return '/sgc_scroll_hero_homepage/static/src/img/frames/frame_' + pad4(i) + '.jpg';
        }

        function drawFrame(i) {
            var img = frameImgs[i];
            if (!img || !img.complete || !img.naturalWidth) {
                return;
            }
            var cw = canvas.width;
            var ch = canvas.height;
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
            ctx.clearRect(0, 0, cw, ch);
            ctx.drawImage(img, sx, sy, sw, sh, 0, 0, cw, ch);
        }

        function resizeCanvas() {
            var dpr = window.devicePixelRatio || 1;
            canvas.width = canvas.clientWidth * dpr;
            canvas.height = canvas.clientHeight * dpr;
            drawFrame(currentFrame);
        }

        function setLoadingProgress(pct) {
            if (loading) {
                loading.style.setProperty('--pct', pct + '%');
                loading.setAttribute('data-pct', pct);
            }
        }

        function preload() {
            var eagerCount = Math.min(15, frameCount);
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

            for (var i = 1; i <= eagerCount; i++) {
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
            }

            var next = eagerCount + 1;
            function lazyStep() {
                if (next > frameCount) {
                    return;
                }
                loadOne(next++);
                (window.requestIdleCallback || setTimeout)(lazyStep, 16);
            }
            lazyStep();
        }

        function animateCaptionOut(beat) {
            if (beat.isFinal) {
                gsap.to(caption, { scale: 0.92, opacity: 0.3, duration: 0.5, ease: 'power2.in' });
            } else {
                gsap.to(caption, { opacity: 0, y: -20, duration: 0.5, ease: 'power2.in' });
            }
        }

        function animateCaptionIn(beat) {
            caption.textContent = beat.text;
            gsap.fromTo(
                caption,
                { opacity: 0, y: 20, scale: 1 },
                { opacity: 1, y: 0, scale: 1, duration: 0.6, ease: 'power2.out' }
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
            gsap.set(searchWrap, { opacity: t, pointerEvents: t > 0.5 ? 'auto' : 'none' });
            if (t > 0 && hint) {
                gsap.set(hint, { opacity: 0 });
            }
        }

        function onScrollUpdate(progress) {
            updateCaption(progress);
            updateFinalReveal(progress);
            var idx = Math.min(frameCount, Math.max(1, Math.round(progress * (frameCount - 1)) + 1));
            currentFrame = idx;
            if (!rafPending) {
                rafPending = true;
                requestAnimationFrame(function () {
                    drawFrame(currentFrame);
                    rafPending = false;
                });
            }
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
                scrub: true,
                onUpdate: function (self) {
                    onScrollUpdate(self.progress);
                }
            });
            instances.set(section, { scrollTrigger: st });
        }

        function startEngine() {
            if (reducedMotion) {
                drawFrame(frameCount);
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
});
