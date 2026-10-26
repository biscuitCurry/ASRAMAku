function confirmLogout(event) {
    event.preventDefault();
    const logoutModal = new bootstrap.Modal(document.getElementById('logoutModal'));
    logoutModal.show();
}

// Turn text into safe HTML before putting it inside a template string
function escapeHtml(value) {
    return String(value == null ? '' : value)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#39;');
}

document.addEventListener('DOMContentLoaded', function() {
    const trigger = document.getElementById('userDropdown');
    const menu = document.getElementById('userDropdownMenu');
    const notifTrigger = document.getElementById('notifBell');
    const notifMenu = document.getElementById('notifDropdown');

    if (notifTrigger && notifMenu) {
        notifTrigger.addEventListener('click', function(event) {
            event.preventDefault();
            event.stopPropagation();
            if (menu) menu.style.display = 'none';
            notifMenu.style.display = (notifMenu.style.display === 'none' || notifMenu.style.display === '') ? 'block' : 'none';
        });
        document.addEventListener('click', function() {
            notifMenu.style.display = 'none';
        });

        function refreshNotifications() {
            fetch('/api/pending-requests/', { headers: { 'Accept': 'application/json' } })
                .then(r => r.ok ? r.json() : null)
                .then(data => {
                    if (!data) return;
                    const badge = document.getElementById('notifBadge');
                    badge.textContent = data.count;
                    badge.style.display = data.count > 0 ? 'inline-grid' : 'none';

                    document.getElementById('notifList').innerHTML = data.items.length
                        ? data.items.map(item => `
                            <a href="/outing/manage/" class="dropdown-item small">
                                <strong>${escapeHtml(item.name)}</strong> — ${escapeHtml(item.destination)}
                                <div class="text-muted" style="font-size:0.75rem;">${escapeHtml(item.time)}</div>
                            </a>`).join('')
                        : '<div class="dropdown-item small text-muted">No pending requests</div>';
                })
                .catch(() => {});
        }

        // The dashboard already has its own stream (and reloads on update), so don't open a second one there
        setInterval(refreshNotifications, 30000);
    }

    if (trigger && menu) {
        // Toggle open/close on click
        trigger.addEventListener('click', function(event) {
            event.preventDefault();
            event.stopPropagation();
            if (notifMenu) notifMenu.style.display = 'none';
            menu.style.display = (menu.style.display === 'none' || menu.style.display === '') ? 'block' : 'none';
        });

        // Close it automatically if user clicks anywhere else on the screen
        document.addEventListener('click', function() {
            menu.style.display = 'none';
        });
    }

    // Corner toasts close on their own after a few seconds
    document.querySelectorAll('#toastStack .alert').forEach(function (toast, i) {
        setTimeout(function () {
            toast.classList.remove('show');
            setTimeout(function () { toast.remove(); }, 200);
        }, 4500 + i * 400);
    });
});

// Stop double submits: lock a form after its first submit, and make "once" links single-use
document.addEventListener('submit', function (e) {
    if (e.defaultPrevented) return;
    const form = e.target;
    if (form.dataset.submitting) { e.preventDefault(); return; }
    form.dataset.submitting = '1';
    setTimeout(function () {
        document.querySelectorAll('button[type=submit]').forEach(function (b) {
            if (b.form === form) b.disabled = true;
        });
    }, 0);
});

document.addEventListener('click', function (e) {
    const link = e.target.closest('a.once');
    if (!link) return;
    if (link.dataset.clicked) { e.preventDefault(); return; }
    link.dataset.clicked = '1';
    link.classList.add('disabled');
});

// If the user comes back with the Back button, unlock everything again
window.addEventListener('pageshow', function () {
    document.querySelectorAll('form[data-submitting]').forEach(function (f) { delete f.dataset.submitting; });
    document.querySelectorAll('button[type=submit]:disabled').forEach(function (b) { b.disabled = false; });
    document.querySelectorAll('a.once').forEach(function (a) { delete a.dataset.clicked; a.classList.remove('disabled'); });
});
