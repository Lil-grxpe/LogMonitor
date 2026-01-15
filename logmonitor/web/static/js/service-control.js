// Service Control & Reports Management for LogMonitor Dashboard

// Charger le statut du service au démarrage
function loadServiceStatus() {
    fetch('/api/service/status')
        .then(response => response.json())
        .then(result => {
            if (result.success) {
                updateServiceStatus(result.running);
            }
        })
        .catch(error => console.error('Erreur statut service:', error))
        ;
}

// Mettre à jour l'affichage du statut
function updateServiceStatus(isRunning) {
    const statusBadge = document.getElementById('service-status');
    if (statusBadge) {
        if (isRunning) {
            statusBadge.innerHTML = '<span class="badge bg-success">🟢 En cours</span>';
        } else {
            statusBadge.innerHTML = '<span class="badge bg-secondary">⚫ Arrêté</span>';
        }
    }
}

// Démarrer le service
function startService() {
    const btn = document.getElementById('btn-start-service');
    btn.disabled = true;
    btn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Démarrage...';

    fetch('/api/service/start', {
        method: 'POST'
    })
        .then(response => response.json())
        .then(result => {
            if (result.success) {
                showNotification('Service démarré avec succès', 'success');
                setTimeout(loadServiceStatus, 1000);
            } else {
                showNotification('Erreur: ' + (result.message || result.error), 'danger');
            }
        })
        .catch(error => {
            showNotification('Erreur: ' + error, 'danger');
        })
        .finally(() => {
            btn.disabled = false;
            btn.innerHTML = '▶️ Démarrer';
        });
}

// Arrêter le service
function stopService() {
    const btn = document.getElementById('btn-stop-service');
    btn.disabled = true;
    btn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Arrêt...';

    fetch('/api/service/stop', {
        method: 'POST'
    })
        .then(response => response.json())
        .then(result => {
            if (result.success) {
                showNotification('Service arrêté avec succès', 'success');
                setTimeout(loadServiceStatus, 1000);
            } else {
                showNotification('Erreur: ' + (result.message || result.error), 'danger');
            }
        })
        .catch(error => {
            showNotification('Erreur: ' + error, 'danger');
        })
        .finally(() => {
            btn.disabled = false;
            btn.innerHTML = '⏹️ Arrêter';
        });
}

// Rafraîchir le statut
function refreshServiceStatus() {
    const btn = document.getElementById('btn-refresh-status');
    btn.disabled = true;
    const originalText = btn.innerHTML;
    btn.innerHTML = '<span class="spinner-border spinner-border-sm"></span>';

    loadServiceStatus();

    setTimeout(() => {
        btn.disabled = false;
        btn.innerHTML = originalText;
    }, 1000);
}

// Générer un rapport
function generateReport(format) {
    const btnId = 'btn-report-' + format;
    const btn = document.getElementById(btnId);
    btn.disabled = true;
    const originalText = btn.innerHTML;
    btn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Génération...';

    fetch('/api/reports/generate', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ format: format })
    })
        .then(response => response.json())
        .then(result => {
            if (result.success && result.filename) {
                showNotification('Rapport généré avec succès', 'success');
                // Télécharger automatiquement
                window.location.href = '/api/reports/download/' + result.filename;
            } else {
                showNotification('Erreur: ' + (result.error || 'Génération échouée'), 'danger');
            }
        })
        .catch(error => {
            showNotification('Erreur: ' + error, 'danger');
        })
        .finally(() => {
            btn.disabled = false;
            btn.innerHTML = originalText;
        });
}

// Afficher une notification
function showNotification(message, type = 'info') {
    const container = document.getElementById('notification-container');
    if (!container) {
        // Créer le conteneur s'il n'existe pas
        const div = document.createElement('div');
        div.id = 'notification-container';
        div.style.position = 'fixed';
        div.style.top = '20px';
        div.style.right = '20px';
        div.style.zIndex = '9999';
        document.body.appendChild(div);
    }

    const notification = document.createElement('div');
    notification.className = `alert alert-${type} alert-dismissible fade show`;
    notification.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;

    document.getElementById('notification-container').appendChild(notification);

    // Auto-supprimer après 5 secondes
    setTimeout(() => {
        notification.remove();
    }, 5000);
}

// Charger au démarrage
document.addEventListener('DOMContentLoaded', function () {
    loadServiceStatus();

    // Rafraîchir le statut toutes les 10 secondes
    setInterval(loadServiceStatus, 10000);
});
