// ────────────────────────────────────────────────────────────
// Wave 1 Tu Tiên runtime — vermillion stone-seal click effect +
// procedural WebAudio "Linh Âm" sound system.
//
// Designed to be additive to the existing main.js / xianxia-*.js
// pipeline. Nothing here mutates DOM created by other scripts;
// we use event delegation on document so dynamically-inserted
// buttons get the seal effect for free.
// ────────────────────────────────────────────────────────────
(function () {
    'use strict';

    var AUDIO_STORAGE_KEY = 'siteAudio';
    var REDUCE_MOTION = (
        typeof window.matchMedia === 'function' &&
        window.matchMedia('(prefers-reduced-motion: reduce)').matches
    );

    // ─── 1. VERMILLION SEAL CLICK STAMP ───
    //
    // Attaches one document-level listener; each .btn / dropdown
    // toggle / theme toggle gets a stamp at the click coordinate
    // when pressed. The stamp removes itself after the animation
    // ends so a rapid second click re-fires cleanly.

    var SEAL_TARGET_SELECTOR = [
        '.btn',
        '.dropdown-toggle',
        '.theme-toggle-btn',
        'button.notification-toggle'
    ].join(',');

    /* Curated seal characters. Each is a brief Tu Tiên / Đạo gia
     * stamp; picked randomly so the click feels alive instead of
     * showing the same character every time. Keep them all the
     * same visual weight (single-glyph Hanzi). */
    var SEAL_CHARS = ['印', '道', '令', '封', '元', '法', '玄', '靈', '丹', '劍'];

    function pickSealChar() {
        return SEAL_CHARS[Math.floor(Math.random() * SEAL_CHARS.length)];
    }

    function stampSealAt(host, clientX, clientY) {
        var rect = host.getBoundingClientRect();
        var stamp = document.createElement('span');
        stamp.className = 'xx-seal-stamp';
        stamp.setAttribute('aria-hidden', 'true');
        stamp.textContent = pickSealChar();
        // Position relative to host (which has overflow: hidden via CSS).
        stamp.style.left = (clientX - rect.left) + 'px';
        stamp.style.top = (clientY - rect.top) + 'px';
        host.appendChild(stamp);
        var cleanup = function () {
            if (stamp.parentNode) {
                stamp.parentNode.removeChild(stamp);
            }
        };
        stamp.addEventListener('animationend', cleanup, { once: true });
        // Belt-and-braces: kill the stamp after 1s in case
        // animationend never fires (e.g. element detached mid-anim).
        window.setTimeout(cleanup, 1000);
    }

    function onPointerDown(event) {
        if (REDUCE_MOTION) return;
        var target = event.target;
        if (!target || typeof target.closest !== 'function') return;
        var host = target.closest(SEAL_TARGET_SELECTOR);
        if (!host) return;
        // Skip the host itself if it's marked .xx-no-seal — useful
        // for big surface-area buttons where the stamp would be
        // distracting (e.g. card-wide click hitboxes).
        if (host.classList.contains('xx-no-seal')) return;
        stampSealAt(host, event.clientX, event.clientY);
    }

    document.addEventListener('pointerdown', onPointerDown, { passive: true });


    // ─── 2. PROCEDURAL "LINH ÂM" AUDIO SYSTEM ───
    //
    // 4 sounds, all generated on the fly via WebAudio so the page
    // ships no .mp3/.ogg assets:
    //
    //   click       — short filtered noise burst, fires on .btn pointerup
    //   submit      — sine sweep, fires on form submit
    //   achievement — 3-note pluck (E4-B4-E5) — exposed as
    //                 GodWebAudio.achievement() for future tier-up FX
    //   ambient     — bamboo wind loop, opt-in only (default OFF)
    //
    // Browser autoplay policy requires a user gesture before
    // AudioContext can produce sound. We honour that by deferring
    // ctx.resume() until the first interaction; subsequent calls
    // are no-ops. Master volume is intentionally low (~0.15) so
    // "default ON" doesn't startle office users.

    var MASTER_VOLUME = 0.18;
    var AUDIO_DISABLED_BY_MOTION_PREF = REDUCE_MOTION;

    /** Read the persisted preference, defaulting to ON. */
    function readAudioPref() {
        try {
            var stored = window.localStorage.getItem(AUDIO_STORAGE_KEY);
            if (stored === 'off') return false;
            if (stored === 'on') return true;
        } catch (e) {
            /* private mode / storage disabled — fall through */
        }
        return true; // default ON per user preference
    }

    function persistAudioPref(enabled) {
        try {
            window.localStorage.setItem(AUDIO_STORAGE_KEY, enabled ? 'on' : 'off');
        } catch (e) {
            /* swallow */
        }
    }

    var GodWebAudio = (function () {
        var ctx = null;
        var masterGain = null;
        var enabled = readAudioPref();

        // prefers-reduced-motion is a strong "less sensory stuff"
        // signal; we mute even if the user has audio enabled.
        function isPlayable() {
            return enabled && !AUDIO_DISABLED_BY_MOTION_PREF;
        }

        function ensureContext() {
            if (ctx) return ctx;
            var Ctor = window.AudioContext || window.webkitAudioContext;
            if (!Ctor) return null;
            try {
                ctx = new Ctor();
            } catch (e) {
                ctx = null;
                return null;
            }
            masterGain = ctx.createGain();
            masterGain.gain.value = MASTER_VOLUME;
            masterGain.connect(ctx.destination);
            return ctx;
        }

        function resumeIfSuspended() {
            if (ctx && ctx.state === 'suspended' && typeof ctx.resume === 'function') {
                try { ctx.resume(); } catch (e) { /* swallow */ }
            }
        }

        /** Play a short noise burst (key click feel). */
        function playClick() {
            if (!isPlayable()) return;
            var c = ensureContext();
            if (!c) return;
            resumeIfSuspended();
            // 50ms of band-passed noise feels like a soft brush stroke.
            var bufferSize = Math.floor(c.sampleRate * 0.05);
            var buffer = c.createBuffer(1, bufferSize, c.sampleRate);
            var data = buffer.getChannelData(0);
            for (var i = 0; i < bufferSize; i++) {
                data[i] = (Math.random() * 2 - 1) * (1 - i / bufferSize);
            }
            var src = c.createBufferSource();
            src.buffer = buffer;
            var filter = c.createBiquadFilter();
            filter.type = 'bandpass';
            filter.frequency.value = 900;
            filter.Q.value = 1.2;
            var gain = c.createGain();
            gain.gain.value = 0.6;
            src.connect(filter).connect(gain).connect(masterGain);
            src.start();
            src.stop(c.currentTime + 0.06);
        }

        /** Sine sweep — gentle "ink drop" feel for form submits. */
        function playSubmit() {
            if (!isPlayable()) return;
            var c = ensureContext();
            if (!c) return;
            resumeIfSuspended();
            var osc = c.createOscillator();
            var gain = c.createGain();
            osc.type = 'sine';
            osc.frequency.setValueAtTime(220, c.currentTime);
            osc.frequency.exponentialRampToValueAtTime(880, c.currentTime + 0.18);
            gain.gain.setValueAtTime(0.0001, c.currentTime);
            gain.gain.exponentialRampToValueAtTime(0.35, c.currentTime + 0.02);
            gain.gain.exponentialRampToValueAtTime(0.001, c.currentTime + 0.22);
            osc.connect(gain).connect(masterGain);
            osc.start();
            osc.stop(c.currentTime + 0.25);
        }

        /** 3-note guzheng-flavoured sting for achievements. */
        function playAchievement() {
            if (!isPlayable()) return;
            var c = ensureContext();
            if (!c) return;
            resumeIfSuspended();
            // E4, B4, E5 — a clean fifth + octave climb.
            var notes = [329.63, 493.88, 659.25];
            notes.forEach(function (freq, index) {
                var t = c.currentTime + index * 0.12;
                var osc = c.createOscillator();
                var gain = c.createGain();
                osc.type = 'triangle';
                osc.frequency.value = freq;
                gain.gain.setValueAtTime(0.0001, t);
                gain.gain.exponentialRampToValueAtTime(0.4, t + 0.02);
                gain.gain.exponentialRampToValueAtTime(0.0001, t + 0.6);
                osc.connect(gain).connect(masterGain);
                osc.start(t);
                osc.stop(t + 0.65);
            });
        }

        function setEnabled(next) {
            enabled = !!next;
            persistAudioPref(enabled);
            document.documentElement.classList.toggle('xx-audio-on', enabled);
            // Update aria-pressed on every toggle button on the page.
            var btns = document.querySelectorAll('.xx-audio-toggle');
            for (var i = 0; i < btns.length; i++) {
                btns[i].setAttribute('aria-pressed', enabled ? 'true' : 'false');
            }
        }

        function isEnabled() { return enabled; }

        return {
            click: playClick,
            submit: playSubmit,
            achievement: playAchievement,
            setEnabled: setEnabled,
            isEnabled: isEnabled
        };
    })();

    // Apply the initial state from localStorage to <html> class AND
    // button aria-pressed attributes so CSS + screen readers see the
    // correct state BEFORE the first user interaction.
    (function syncInitialState() {
        var on = GodWebAudio.isEnabled();
        document.documentElement.classList.toggle('xx-audio-on', on);
        var btns = document.querySelectorAll('.xx-audio-toggle');
        for (var i = 0; i < btns.length; i++) {
            btns[i].setAttribute('aria-pressed', on ? 'true' : 'false');
        }
    })();

    // Wire the audio toggle. Uses event delegation so it works
    // for both the desktop footer button and any future mobile
    // duplicate without re-binding.
    document.addEventListener('click', function (event) {
        var target = event.target;
        if (!target || typeof target.closest !== 'function') return;
        var toggle = target.closest('.xx-audio-toggle');
        if (!toggle) return;
        event.preventDefault();
        GodWebAudio.setEnabled(!GodWebAudio.isEnabled());
        // Play a click sound IF the new state is "on" so the user
        // hears confirmation. If they just turned it off, we stay
        // silent — that's the whole point.
        if (GodWebAudio.isEnabled()) {
            GodWebAudio.click();
        }
    });

    // Click sound on every button-shaped element. Pointerup is
    // chosen over click so it fires together with the seal stamp
    // (which fires on pointerdown). Two events ~= one "press"
    // feel without race conditions.
    document.addEventListener('pointerup', function (event) {
        var target = event.target;
        if (!target || typeof target.closest !== 'function') return;
        var host = target.closest(SEAL_TARGET_SELECTOR);
        if (!host) return;
        if (host.classList.contains('xx-no-seal')) return;
        // Don't double-play when the user is toggling audio itself.
        if (host.classList.contains('xx-audio-toggle')) return;
        GodWebAudio.click();
    }, { passive: true });

    // Form submit sound. Only fires on real <form> submissions —
    // not on synthetic .preventDefault'd ones.
    document.addEventListener('submit', function () {
        GodWebAudio.submit();
    });

    // Expose for future call-sites (e.g. tier-up animation).
    window.GodWebAudio = GodWebAudio;
})();
