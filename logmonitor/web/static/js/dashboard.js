// Initialiser les graphiques
let alertsChart = null;
let severityChart = null;

// Fonction utilitaire pour les badges de sévérité
function getSeverityBadge(severity) {
    const badges = {
        'emergency': 'bg-dark',
        'alert': 'bg-danger',
        'critical': 'bg-danger',
        'error': 'bg-warning text-dark',
        'high': 'bg-warning text-dark',
        'warning': 'bg-warning text-dark',
        'medium': 'bg-primary',
        'notice': 'bg-info text-dark',
        'low': 'bg-info text-dark',
        'info': 'bg-secondary',
        'debug': 'bg-light text-dark'
    };
    return `<span class="badge ${badges[severity] || 'bg-secondary'}">${severity.toUpperCase()}</span>`;
}

// Charger les statistiques KPIs
function loadStats() {
    fetch('/api/stats')
        .then(response => response.json())
        .then(result => {
            if (result.success) {
                document.getElementById('total-logs').textContent = result.data.total_logs;
                document.getElementById('total-alerts').textContent = result.data.total_alerts;

                const critical = result.data.alerts_by_severity?.critical || 0;
                document.getElementById('critical-alerts').textContent = critical;
            }
        })
        .catch(error => console.error('Erreur lors du chargement des stats:', error));
}

// Charger le graphique des alertes par heure
function loadAlertsChart() {
    fetch('/api/alerts/by-hour')
        .then(response => response.json())
        .then(result => {
            if (result.success) {
                const ctx = document.getElementById('alertsChart').getContext('2d');

                if (alertsChart) {
                    alertsChart.destroy();
                }

                alertsChart = new Chart(ctx, {
                    type: 'line',
                    data: {
                        labels: result.labels,
                        datasets: [{
                            label: 'Alertes',
                            data: result.data,
                            borderColor: '#4e73df',
                            backgroundColor: 'rgba(78, 115, 223, 0.05)',
                            tension: 0.3,
                            fill: true
                        }]
                    },
                    options: {
                        maintainAspectRatio: false,
                        responsive: true,
                        plugins: {
                            legend: {
                                display: false
                            }
                        },
                        scales: {
                            y: {
                                beginAtZero: true,
                                ticks: {
                                    stepSize: 1
                                }
                            },
                            x: {
                                grid: {
                                    display: false
                                }
                            }
                        }
                    }
                });
            }
        })
        .catch(error => console.error('Erreur lors du chargement du graphique:', error));
}

// Charger le graphique de répartition par sévérité
function loadSeverityChart() {
    fetch('/api/alerts/by-severity')
        .then(response => response.json())
        .then(result => {
            if (result.success) {
                const ctx = document.getElementById('severityChart').getContext('2d');

                if (severityChart) {
                    severityChart.destroy();
                }

                // Définition de toutes les sévérités dans l'ordre
                const allSeverities = [
                    'emergency', 'alert', 'critical', 'error',
                    'warning', 'notice', 'info', 'debug'
                ];

                const colors = {
                    'emergency': '#721c24', // Sang foncé
                    'alert': '#dc3545',     // Rouge vif
                    'critical': '#dc3545',  // Rouge vif
                    'error': '#fd7e14',     // Orange foncé
                    'high': '#fd7e14',      // Orange foncé (alias)
                    'warning': '#ffc107',   // Jaune
                    'medium': '#ffc107',    // Jaune (alias)
                    'notice': '#0d6efd',    // Bleu
                    'low': '#0dcaf0',       // Cyan (alias)
                    'info': '#6c757d',      // Gris
                    'debug': '#adb5bd'      // Gris clair
                };

                // Préparer les données en incluant 0 pour ceux qui manquent
                // On fusionne les résultats de l'API avec notre liste complète
                const dataMap = {};

                // Mapper les aliases si nécessaire
                const apiData = result.data.reduce((acc, val, idx) => {
                    const label = result.labels[idx];
                    acc[label] = val;
                    return acc;
                }, {});

                // Construire les tableaux finaux
                const labels = [];
                const data = [];
                const bgColors = [];

                allSeverities.forEach(severity => {
                    // Gérer les alias (ex: high -> error)
                    let count = apiData[severity] || 0;

                    if (severity === 'error') count += apiData['high'] || 0;
                    if (severity === 'warning') count += apiData['medium'] || 0;
                    if (severity === 'notice') count += apiData['low'] || 0;

                    labels.push(severity.charAt(0).toUpperCase() + severity.slice(1));
                    data.push(count);
                    bgColors.push(colors[severity]);
                });

                severityChart = new Chart(ctx, {
                    type: 'doughnut',
                    data: {
                        labels: labels,
                        datasets: [{
                            data: data,
                            backgroundColor: bgColors,
                            borderWidth: 1
                        }]
                    },
                    options: {
                        maintainAspectRatio: false,
                        responsive: true,
                        plugins: {
                            legend: {
                                position: 'right', // Légende à droite pour mieux voir la liste
                                labels: {
                                    usePointStyle: true,
                                    padding: 15,
                                    boxWidth: 10
                                }
                            },
                            title: {
                                display: true,
                                text: 'Répartition par Sévérité'
                            }
                        },
                        cutout: '60%'
                    }
                });
            }
        })
        .catch(error => console.error('Erreur lors du chargement du graphique sévérité:', error));
}

// Charger les dernières alertes
function loadLatestAlerts() {
    fetch('/api/alerts/latest?limit=10')
        .then(response => response.json())
        .then(result => {
            if (result.success) {
                const tbody = document.getElementById('alerts-table-body');
                tbody.innerHTML = '';

                if (result.data.length === 0) {
                    tbody.innerHTML = '<tr><td colspan="4" class="text-center">Aucune alerte</td></tr>';
                    return;
                }

                result.data.forEach(alert => {
                    const row = document.createElement('tr');

                    // Formater la date
                    const timestamp = new Date(alert.timestamp);
                    const timeStr = timestamp.toLocaleTimeString('fr-FR');

                    row.innerHTML = `
                        <td>${timeStr}</td>
                        <td>${getSeverityBadge(alert.severity)}</td>
                        <td><small>${alert.rule_name}</small></td>
                        <td><small>${alert.description}</small></td>
                    `;

                    tbody.appendChild(row);
                });
            }
        })
        .catch(error => console.error('Erreur lors du chargement des alertes:', error));
}

// Charger les top IPs
function loadTopIPs() {
    fetch('/api/top-ips')
        .then(response => response.json())
        .then(result => {
            if (result.success) {
                const list = document.getElementById('top-ips-list');
                list.innerHTML = '';

                if (result.data.length === 0) {
                    list.innerHTML = '<li class="list-group-item">Aucune IP suspecte</li>';
                    return;
                }

                result.data.forEach(item => {
                    const li = document.createElement('li');
                    li.className = 'list-group-item d-flex justify-content-between align-items-center';
                    li.innerHTML = `
                        <small><code>${item.source_ip}</code></small>
                        <span class="badge bg-danger rounded-pill">${item.count}</span>
                    `;
                    list.appendChild(li);
                });
            }
        })
        .catch(error => console.error('Erreur lors du chargement des IPs:', error));
}

// Fonction de génération de rapport
function generateReport(format) {
    const btnId = `btn-report-${format}`;
    const btn = document.getElementById(btnId);
    const originalText = btn.textContent;

    // Désactiver le bouton et montrer le chargement
    btn.disabled = true;
    btn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Génération...';

    fetch('/api/reports/generate', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ format: format })
    })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Créer un lien temporaire pour le téléchargement
                window.location.href = data.download_url;

                // Afficher une notification de succès (optionnel)
                alert(`Rapport ${format.toUpperCase()} généré avec succès !`);
            } else {
                alert('Erreur: ' + (data.error || 'Erreur inconnue'));
            }
        })
        .catch(error => {
            console.error('Erreur:', error);
            alert('Erreur lors de la communication avec le serveur');
        })
        .finally(() => {
            // Rétablir le bouton
            btn.disabled = false;
            btn.textContent = originalText;
        });
}


// Rafraîchir toutes les données
function refreshDashboard() {
    loadStats();
    loadAlertsChart();
    loadSeverityChart();
    loadLatestAlerts();
    loadTopIPs();
}

// Charger au démarrage
document.addEventListener('DOMContentLoaded', function () {
    refreshDashboard();

    // Rafraîchir toutes les 5 secondes
    setInterval(refreshDashboard, 5000);
});
