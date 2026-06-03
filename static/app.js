// Private Toolbox — minimal client-side helpers.
// Active sidebar highlighting is handled server-side; this is kept small on purpose.
document.addEventListener('DOMContentLoaded', function () {
    // Auto-dismiss flash messages after a few seconds.
    document.querySelectorAll('.alert').forEach(function (el) {
        setTimeout(function () {
            el.style.transition = 'opacity 0.4s';
            el.style.opacity = '0';
            setTimeout(function () { el.remove(); }, 400);
        }, 5000);
    });
});
