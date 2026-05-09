// Admin "ting tinh" alert: chimes while there are pending top-up requests,
// stops as soon as every pending request has been approved or rejected.

(function () {
    var POLL_URL = '/admin/api/pending-topups-count';
    var POLL_INTERVAL_MS = 5000;
    var CHIME_INTERVAL_MS = 3500;

    var audioCtx = null;
    var alarmTimer = null;
    var pollTimer = null;
    var basePageTitle = document.title;
    var titleFlashState = false;
    var titleFlashTimer = null;
    var currentCount = 0;

    function ensureAudioContext() {
        if (audioCtx === null) {
            var Ctor = window.AudioContext || window.webkitAudioContext;
            if (!Ctor) {
                return null;
            }
            try {
                audioCtx = new Ctor();
            } catch (err) {
                audioCtx = null;
                return null;
            }
        }
        if (audioCtx.state === 'suspended' && typeof audioCtx.resume === 'function') {
            audioCtx.resume();
        }
        return audioCtx;
    }

    function unlockAudioOnce() {
        ensureAudioContext();
    }

    document.addEventListener('click', unlockAudioOnce, true);
    document.addEventListener('keydown', unlockAudioOnce, true);
    document.addEventListener('touchstart', unlockAudioOnce, true);

    function playTone(ctx, freq, startOffset, duration) {
        var osc = ctx.createOscillator();
        var gain = ctx.createGain();
        osc.type = 'sine';
        osc.frequency.value = freq;
        var start = ctx.currentTime + startOffset;
        gain.gain.setValueAtTime(0, start);
        gain.gain.linearRampToValueAtTime(0.35, start + 0.03);
        gain.gain.exponentialRampToValueAtTime(0.001, start + duration);
        osc.connect(gain).connect(ctx.destination);
        osc.start(start);
        osc.stop(start + duration + 0.05);
    }

    function playTingTinh() {
        var ctx = ensureAudioContext();
        if (!ctx || ctx.state !== 'running') {
            return;
        }
        playTone(ctx, 1175, 0, 0.45);    // "ting" (D6)
        playTone(ctx, 1568, 0.22, 0.55); // "tinh" (G6)
    }

    function flashTitleTick() {
        if (currentCount <= 0) {
            return;
        }
        titleFlashState = !titleFlashState;
        if (titleFlashState) {
            document.title = '(' + currentCount + ') Yêu cầu nạp mới! - ' + basePageTitle;
        } else {
            document.title = basePageTitle;
        }
    }

    function startAlarm() {
        if (alarmTimer) {
            return;
        }
        playTingTinh();
        alarmTimer = setInterval(playTingTinh, CHIME_INTERVAL_MS);
        if (!titleFlashTimer) {
            titleFlashTimer = setInterval(flashTitleTick, 1000);
        }
    }

    function stopAlarm() {
        if (alarmTimer) {
            clearInterval(alarmTimer);
            alarmTimer = null;
        }
        if (titleFlashTimer) {
            clearInterval(titleFlashTimer);
            titleFlashTimer = null;
        }
        document.title = basePageTitle;
        titleFlashState = false;
    }

    function pollPendingTopups() {
        fetch(POLL_URL, { credentials: 'same-origin', cache: 'no-store' })
            .then(function (resp) {
                if (!resp.ok) {
                    return null;
                }
                return resp.json();
            })
            .then(function (data) {
                if (!data) {
                    return;
                }
                currentCount = data.count || 0;
                if (currentCount > 0) {
                    startAlarm();
                } else {
                    stopAlarm();
                }
            })
            .catch(function () { /* network errors are ignored; next poll retries */ });
    }

    document.addEventListener('DOMContentLoaded', function () {
        basePageTitle = document.title;
        pollPendingTopups();
        pollTimer = setInterval(pollPendingTopups, POLL_INTERVAL_MS);
    });

    window.addEventListener('beforeunload', function () {
        stopAlarm();
        if (pollTimer) {
            clearInterval(pollTimer);
            pollTimer = null;
        }
    });
})();
