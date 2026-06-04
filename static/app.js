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

function escapeHtml(str) {
    return str.replace(/[&<>"']/g, function (c) {
        return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
    });
}
