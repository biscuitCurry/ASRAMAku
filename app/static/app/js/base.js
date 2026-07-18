function confirmLogout(event) {
    event.preventDefault();
    const logoutModal = new bootstrap.Modal(document.getElementById('logoutModal'));
    logoutModal.show();
}

document.addEventListener('DOMContentLoaded', function() {
    const trigger = document.getElementById('userDropdown');
    const menu = document.getElementById('userDropdownMenu');

    if (trigger && menu) {
        // Toggle open/close on click
        trigger.addEventListener('click', function(event) {
            event.preventDefault();
            event.stopPropagation();
            menu.style.display = (menu.style.display === 'none' || menu.style.display === '') ? 'block' : 'none';
        });

        // Close it automatically if user clicks anywhere else on the screen
        document.addEventListener('click', function() {
            menu.style.display = 'none';
        });
    }
});