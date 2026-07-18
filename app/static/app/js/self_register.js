$(document).ready(function () {
    // 1. Core DOM Elements
    const registerForm = document.querySelector('form'),
          registerSubmitBtn = document.querySelector('button[type="submit"]'),
          body = document.querySelector('body');

    if (!registerForm) return;

    // Set matching ID tag so the background logic can uniquely identify this transaction
    registerForm.setAttribute('id', 'student-self-registration-form');

    // 2. Connectivity Listeners
    window.addEventListener('offline', () => {
        console.log('App switched to offline mode. Registration will hold locally.');
    });

    window.addEventListener('online', () => {
        if (navigator.serviceWorker) {
            navigator.serviceWorker.ready.then((registration) => {
                return registration.sync.register('sync-offline-data');
            }).catch((err) => console.error('Background Sync setup failed:', err));
        }
    });

    if (navigator.serviceWorker) {
        navigator.serviceWorker.addEventListener('message', event => {
            window.location.reload();
        });
    }

    // 3. Form Value Extraction Matrix
    function captureFormData(gotForm) {
        const formData = new FormData(gotForm);
        const data = {};

        formData.forEach((value, key) => {
            if (key !== 'csrfmiddlewaretoken') {
                data[key] = value;
            }
        });

        data['target'] = gotForm.id;
        return data;
    }

    // 4. IndexedDB Storage Core
    function openDatabase() {
        return new Promise((resolve, reject) => {
            const request = indexedDB.open('offlineDataStore', 1);

            request.onsuccess = function (event) {
                const db = event.target.result;
                resolve(db);
            };

            request.onerror = function (event) {
                reject(event.target.error);
            };

            request.onupgradeneeded = function (event) {
                const db = event.target.result;
                if (!db.objectStoreNames.contains('data')) {
                    const store = db.createObjectStore('data', { keyPath: 'id', autoIncrement: true });
                    store.createIndex('targetIndex', 'target', { unique: false });
                }
            };
        });
    }

    function storeDataOffline(data) {
        openDatabase().then((db) => {
            const transaction = db.transaction('data', 'readwrite');
            const store = transaction.objectStore('data');

            store.add(data);

            transaction.oncomplete = function () {
                console.log('Student dataset queued offline!');
                alert('You are offline. Your student profile has been saved in the browser queue and will sync to the hostel database automatically upon reconnection!');
                registerForm.reset(); 
            };

            transaction.onerror = function () {
                console.log('Error caching data locally!');
            };
        }).catch((error) => {
            console.error('Database connection error:', error);
        });
    }

    // 5. CSRF Acquisition Middleware 
    function getCSRFToken() {
        var cookieValue = null;
        if (document.cookie && document.cookie != '') {
            var cookies = document.cookie.split(';');
            for (var i = 0; i < cookies.length; i++) {
                var cookie = jQuery.trim(cookies[i]);
                if (cookie.substring(0, 10) == ('csrftoken' + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(10));
                    break;
                }
            }
        }
        return cookieValue;
    }

    var csrfToken = getCSRFToken();

    // 6. Request Interception Pipeline
    registerForm.addEventListener('submit', async (event) => {
        event.preventDefault();

        if (navigator.onLine === false) {
            // Offline Branch: Hold details in browser IndexedDB cache
            storeDataOffline(captureFormData(registerForm));
        } else {
            // Online Branch: Post to the proper registration endpoint
            const formData = new FormData(registerForm);

            try {
                // FIXED: Changed endpoint path to target your actual registration view route
                const response = await fetch('/register/', {
                    method: 'POST',
                    headers: {
                        'X-CSRFToken': csrfToken,
                    },
                    body: formData,
                });

                if (response.ok) {
                    // Redirect back to login/index page on success as per register view definition
                    window.location.href = window.location.origin + '/';
                } else {
                    // Standard structural form error fallback redirection
                    registerForm.submit();
                }
            } catch (error) {
                console.error('API Pipeline execution failure:', error);
                registerForm.submit();
            }
        }
    });
});