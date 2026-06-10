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

    // Ask for confirmation before submitting any form with a data-confirm message
    // (used by the Archive buttons on PDF Splitter and PDF Merger).
    document.querySelectorAll('form[data-confirm]').forEach(function (form) {
        form.addEventListener('submit', function (e) {
            if (!window.confirm(form.getAttribute('data-confirm'))) {
                e.preventDefault();
            }
        });
    });

    initThemeToggle();
    initSidebarAccordion();
    initPdfMerger();
    initSecureKeyGenerator();
});

// ---- Theme toggle ----
// The initial theme is set by an inline script in <head> (before paint). Here we
// only flip the data-theme attribute on click and persist the choice.
function initThemeToggle() {
    var btn = document.getElementById('theme-toggle');
    if (!btn) return;
    btn.addEventListener('click', function () {
        var current = document.documentElement.getAttribute('data-theme') === 'dark' ? 'dark' : 'light';
        var next = current === 'dark' ? 'light' : 'dark';
        document.documentElement.setAttribute('data-theme', next);
        try { localStorage.setItem('theme', next); } catch (e) {}
    });
}

// ---- Sidebar accordion ----
// Single-open: clicking a category header expands it and collapses the others,
// keeping the sidebar compact. The category for the current page starts open
// (server-rendered); on the home page we open the first category by default.
function initSidebarAccordion() {
    var groups = Array.prototype.slice.call(document.querySelectorAll('.nav-group'));
    if (!groups.length) return;

    if (!groups.some(function (g) { return g.classList.contains('open'); })) {
        groups[0].classList.add('open');
    }

    groups.forEach(function (group) {
        var header = group.querySelector('.nav-group-header');
        if (!header) return;
        header.addEventListener('click', function () {
            var isOpen = group.classList.contains('open');
            groups.forEach(function (g) { g.classList.remove('open'); });
            if (!isOpen) group.classList.add('open');
        });
    });
}

// ---- PDF Merger: file list with reorder / remove ----
// Maintains a selectedFiles array and syncs it back to the file input via a
// DataTransfer so the server receives the files in the visible order.
function initPdfMerger() {
    var fileInput = document.getElementById('files');
    var list = document.getElementById('file-list');
    var emptyMsg = document.getElementById('file-list-empty');
    if (!fileInput || !list) return; // not on the merger page

    var selectedFiles = [];

    function formatSize(bytes) {
        if (bytes < 1024) return bytes + ' B';
        if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
        return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
    }

    function sameFile(a, b) {
        return a.name === b.name && a.size === b.size && a.lastModified === b.lastModified;
    }

    function syncInput() {
        var dt = new DataTransfer();
        selectedFiles.forEach(function (f) { dt.items.add(f); });
        fileInput.files = dt.files;
    }

    function render() {
        list.innerHTML = '';
        if (selectedFiles.length === 0) {
            emptyMsg.style.display = '';
            return;
        }
        emptyMsg.style.display = 'none';

        selectedFiles.forEach(function (file, i) {
            var li = document.createElement('li');
            li.className = 'file-item';

            var info = document.createElement('div');
            info.className = 'file-info';
            info.innerHTML = '<span class="file-name">' + (i + 1) + '. ' + escapeHtml(file.name) +
                '</span><span class="file-size">' + formatSize(file.size) + '</span>';

            var actions = document.createElement('div');
            actions.className = 'file-actions';
            actions.appendChild(makeBtn('↑', 'Move up', i === 0, function () { move(i, -1); }));
            actions.appendChild(makeBtn('↓', 'Move down', i === selectedFiles.length - 1, function () { move(i, 1); }));
            actions.appendChild(makeBtn('✕', 'Remove', false, function () { removeAt(i); }, 'remove'));

            li.appendChild(info);
            li.appendChild(actions);
            list.appendChild(li);
        });
    }

    function makeBtn(text, title, disabled, onClick, extraClass) {
        var b = document.createElement('button');
        b.type = 'button';
        b.className = 'file-btn' + (extraClass ? ' file-btn-' + extraClass : '');
        b.textContent = text;
        b.title = title;
        b.disabled = disabled;
        b.addEventListener('click', onClick);
        return b;
    }

    function move(i, dir) {
        var j = i + dir;
        if (j < 0 || j >= selectedFiles.length) return;
        var tmp = selectedFiles[i];
        selectedFiles[i] = selectedFiles[j];
        selectedFiles[j] = tmp;
        render();
        syncInput();
    }

    function removeAt(i) {
        selectedFiles.splice(i, 1);
        render();
        syncInput();
    }

    fileInput.addEventListener('change', function () {
        Array.prototype.forEach.call(fileInput.files, function (f) {
            if (!f.name.toLowerCase().endsWith('.pdf')) return; // PDFs only
            var dup = selectedFiles.some(function (e) { return sameFile(e, f); });
            if (!dup) selectedFiles.push(f);
        });
        render();
        syncInput();
    });

    render();
}

// ---- Secure Key Generator ----
// Presets only *fill in* settings; editing any field flips the preset back to
// "other". Mode selection shows the relevant option group. Results support
// per-value hide/reveal and copy, plus copy-as-format. Nothing is persisted.
function initSecureKeyGenerator() {
    var form = document.getElementById('skg-form');
    if (!form) return; // not on the key generator page

    var presetSelect = document.getElementById('preset');
    var modeSelect = document.getElementById('mode');
    var outputSelect = document.getElementById('output_template');
    var presets = readJson('skg-presets') || {};
    var applyingPreset = false;

    // Map preset setting keys that don't line up 1:1 with a form control name.
    function setField(name, value) {
        if (name === 'base64_urlsafe') {
            var bv = form.querySelector('[name="base64_variant"]');
            if (bv) bv.value = value ? 'urlsafe' : 'standard';
            return;
        }
        var el = form.querySelector('[name="' + name + '"]');
        if (!el) return;
        if (el.type === 'checkbox') {
            el.checked = Boolean(value);
        } else {
            el.value = value;
        }
    }

    function applyPreset(key) {
        var preset = presets[key];
        if (!preset) return;
        applyingPreset = true;
        Object.keys(preset.settings).forEach(function (k) {
            setField(k, preset.settings[k]);
        });
        applyingPreset = false;
        updateModeVisibility();
        updateOutputVisibility();
        updatePresetHelp();
    }

    function updatePresetHelp() {
        var help = document.getElementById('preset-help');
        if (!help) return;
        var preset = presets[presetSelect.value];
        if (preset && preset.help) {
            help.textContent = preset.help + ' You can still edit everything below.';
        } else {
            help.textContent = 'Custom settings. Pick a preset to load defaults for a use case.';
        }
    }

    function updateModeVisibility() {
        var mode = modeSelect.value;
        form.querySelectorAll('[data-mode-group]').forEach(function (group) {
            var modes = group.getAttribute('data-mode-group').split(' ');
            var show = modes.indexOf('all') !== -1 || modes.indexOf(mode) !== -1;
            group.style.display = show ? '' : 'none';
        });
        // Per-mode hint lines and sub-options inside shared groups.
        form.querySelectorAll('[data-mode-hint]').forEach(function (el) {
            el.style.display = el.getAttribute('data-mode-hint') === mode ? '' : 'none';
        });
        form.querySelectorAll('[data-mode-sub]').forEach(function (el) {
            el.style.display = el.getAttribute('data-mode-sub') === mode ? '' : 'none';
        });
    }

    function updateOutputVisibility() {
        var needsName = ['env', 'json', 'yaml', 'java', 'python'];
        var grp = form.querySelector('[data-varname-group]');
        if (grp) grp.style.display = needsName.indexOf(outputSelect.value) !== -1 ? '' : 'none';
    }

    presetSelect.addEventListener('change', function () {
        if (presetSelect.value !== 'other') applyPreset(presetSelect.value);
        else updatePresetHelp();
    });

    // Any manual edit flips the preset selector to "other".
    form.addEventListener('input', flipToOther);
    form.addEventListener('change', flipToOther);
    function flipToOther(e) {
        if (applyingPreset) return;
        if (e.target === presetSelect) return;
        if (presetSelect.value !== 'other') {
            presetSelect.value = 'other';
            updatePresetHelp();
        }
    }

    modeSelect.addEventListener('change', updateModeVisibility);
    outputSelect.addEventListener('change', updateOutputVisibility);

    updateModeVisibility();
    updateOutputVisibility();
    updatePresetHelp();

    initSkgResult();
    skgScrollToOutcome();
}

// After a generation the page re-renders; land the user on what they need to see.
// On an error, go to the error message; otherwise go to the results. On the
// first (GET) load there is neither, so the page stays at the top as normal.
function skgScrollToOutcome() {
    var error = document.getElementById('skg-error');
    if (error) {
        error.scrollIntoView({ behavior: 'smooth', block: 'center' });
        error.focus({ preventScroll: true });
        return;
    }
    var result = document.getElementById('skg-result');
    if (result) {
        result.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
}

function initSkgResult() {
    var result = document.getElementById('skg-result');
    if (!result) return;

    var hideByDefault = result.getAttribute('data-hide') === 'true';
    var status = document.getElementById('copy-status');

    function flash(msg) {
        if (!status) return;
        status.textContent = msg;
        setTimeout(function () { status.textContent = ''; }, 2500);
    }

    // Masking is purely visual: the real value always lives in data-secret (rows)
    // and in the `formats` JSON (preview), so copy buttons copy the true value
    // even while everything on screen is masked.

    // ---- Per-value rows: each can be peeked individually ----
    var rowControllers = [];
    result.querySelectorAll('.key-row').forEach(function (row) {
        var code = row.querySelector('.key-value');
        var secret = code.getAttribute('data-secret');
        var masked = '•'.repeat(Math.min(secret.length, 32));
        var revealBtn = row.querySelector('.js-reveal');
        var hidden = hideByDefault;

        function apply() {
            code.textContent = hidden ? masked : secret;
            if (revealBtn) {
                revealBtn.setAttribute('aria-pressed', String(!hidden));
                revealBtn.setAttribute('aria-label', hidden ? 'Reveal value' : 'Hide value');
            }
        }
        apply();

        if (revealBtn) {
            revealBtn.addEventListener('click', function () { hidden = !hidden; apply(); });
        }
        var copyOne = row.querySelector('.js-copy-one');
        if (copyOne) {
            copyOne.addEventListener('click', function () {
                copyText(secret, function (ok) { flash(ok ? 'Copied value.' : 'Copy failed.'); });
            });
        }
        // Let the master toggle drive this row too.
        rowControllers.push(function (h) { hidden = h; apply(); });
    });

    // ---- Formatted preview: masked twin swapped in when hidden ----
    var formats = readJson('skg-formats') || {};
    var formatsMasked = readJson('skg-formats-masked') || {};
    var display = document.getElementById('format-display');
    var copyAll = document.getElementById('copy-formatted');
    var tabs = result.querySelectorAll('.format-tab');
    var previewHidden = hideByDefault;
    var currentFmt = null;

    function renderPreview() {
        if (currentFmt === null) return;
        var src = previewHidden ? formatsMasked : formats;
        if (src[currentFmt] !== undefined) display.textContent = src[currentFmt];
    }

    function showFormat(fmt) {
        if (formats[fmt] === undefined) return;
        currentFmt = fmt;
        tabs.forEach(function (t) {
            t.classList.toggle('active', t.getAttribute('data-format') === fmt);
        });
        renderPreview();
    }

    tabs.forEach(function (tab) {
        tab.addEventListener('click', function () { showFormat(tab.getAttribute('data-format')); });
    });

    // Start on the format the user selected (falling back to plain list).
    var initial = window.SKG_SELECTED_FORMAT;
    if (initial === 'plain') initial = 'plain_list';
    if (formats[initial] === undefined) initial = 'plain_list';
    showFormat(initial);

    if (copyAll) {
        copyAll.addEventListener('click', function () {
            // Always copy the real formatted output, regardless of mask state.
            var text = formats[currentFmt];
            copyText(text, function (ok) { flash(ok ? 'Copied all values.' : 'Copy failed.'); });
        });
    }

    // ---- Master toggle: reveal / hide every visible area at once ----
    var master = document.getElementById('master-reveal');
    var allHidden = hideByDefault;
    function applyMaster() {
        rowControllers.forEach(function (set) { set(allHidden); });
        previewHidden = allHidden;
        renderPreview();
        if (master) {
            master.setAttribute('aria-pressed', String(!allHidden));
            master.textContent = allHidden ? '👁 Reveal all' : '🙈 Hide all';
        }
    }
    if (master) {
        master.addEventListener('click', function () { allHidden = !allHidden; applyMaster(); });
        applyMaster(); // sets the correct initial label
    }
}

// Read a <script type="application/json"> payload by id.
function readJson(id) {
    var el = document.getElementById(id);
    if (!el) return null;
    try { return JSON.parse(el.textContent); } catch (e) { return null; }
}

// Copy helper with a graceful fallback for non-secure / older contexts.
function copyText(text, done) {
    function fallback() {
        try {
            var ta = document.createElement('textarea');
            ta.value = text;
            ta.style.position = 'fixed';
            ta.style.opacity = '0';
            document.body.appendChild(ta);
            ta.focus();
            ta.select();
            var ok = document.execCommand('copy');
            document.body.removeChild(ta);
            done(ok);
        } catch (e) { done(false); }
    }
    if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(text).then(function () { done(true); }, fallback);
    } else {
        fallback();
    }
}

function escapeHtml(str) {
    return str.replace(/[&<>"']/g, function (c) {
        return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
    });
}
