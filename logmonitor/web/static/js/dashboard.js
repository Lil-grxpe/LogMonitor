let alertsChart = null;
let severityChart = null;

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

function loadStats() {
    fetch('/api/stats')
        .then(response => response.json())
        .then(result => {
            if (result.success) {
                document.getElementById('total-logs').textContent = result.data.total_logs.toLocaleString();
                document.getElementById('total-alerts').textContent = result.data.total_alerts.toLocaleString();
                const critical = result.data.alerts_by_severity?.critical || 0;
                document.getElementById('critical-alerts').textContent = critical.toLocaleString();
            }
        })
        .catch(error => console.error(error));
}

function loadAlertsChart() {
    fetch('/api/alerts/by-hour')
        .then(response => response.json())
        .then(result => {
            if (result.success) {
                const ctx = document.getElementById('alertsChart').getContext('2d');

                if (alertsChart) {
                    alertsChart.destroy();
                }

                const gradient = ctx.createLinearGradient(0, 0, 0, 300);
                gradient.addColorStop(0, 'rgba(59, 130, 246, 0.3)');
                gradient.addColorStop(1, 'rgba(59, 130, 246, 0)');

                alertsChart = new Chart(ctx, {
                    type: 'line',
                    data: {
                        labels: result.labels,
                        datasets: [{
                            label: 'Alertes',
                            data: result.data,
                            borderColor: '#3b82f6',
                            backgroundColor: gradient,
                            borderWidth: 3,
                            tension: 0.4,
                            fill: true,
                            pointBackgroundColor: '#3b82f6',
                            pointBorderColor: '#1e293b',
                            pointBorderWidth: 2,
                            pointRadius: 4,
                            pointHoverRadius: 6
                        }]
                    },
                    options: {
                        maintainAspectRatio: false,
                        responsive: true,
                        resizeDelay: 200,
                        interaction: {
                            intersect: false,
                            mode: 'index'
                        },
                        plugins: {
                            legend: {
                                display: false
                            },
                            tooltip: {
                                backgroundColor: '#1e293b',
                                titleColor: '#f1f5f9',
                                bodyColor: '#94a3b8',
                                borderColor: '#334155',
                                borderWidth: 1,
                                padding: 12,
                                cornerRadius: 8
                            }
                        },
                        scales: {
                            y: {
                                beginAtZero: true,
                                grid: {
                                    color: 'rgba(51, 65, 85, 0.5)',
                                    drawBorder: false
                                },
                                ticks: {
                                    color: '#94a3b8',
                                    stepSize: 1,
                                    font: {
                                        size: 11
                                    }
                                }
                            },
                            x: {
                                grid: {
                                    display: false
                                },
                                ticks: {
                                    color: '#94a3b8',
                                    font: {
                                        size: 11
                                    }
                                }
                            }
                        },
                        onResize: function (chart, size) {
                            if (chart.canvas.parentNode.clientHeight === 300) {
                                return;
                            }
                        }
                    }
                });
            }
        })
        .catch(error => console.error(error));
}

function loadSeverityChart() {
    fetch('/api/alerts/by-severity')
        .then(response => response.json())
        .then(result => {
            if (result.success) {
                const ctx = document.getElementById('severityChart').getContext('2d');

                if (severityChart) {
                    severityChart.destroy();
                }

                const allSeverities = [
                    'emergency', 'alert', 'critical', 'error',
                    'warning', 'notice', 'info', 'debug'
                ];

                const colors = {
                    'emergency': '#7f1d1d',
                    'alert': '#dc2626',
                    'critical': '#ef4444',
                    'error': '#f97316',
                    'high': '#f97316',
                    'warning': '#eab308',
                    'medium': '#eab308',
                    'notice': '#3b82f6',
                    'low': '#06b6d4',
                    'info': '#64748b',
                    'debug': '#94a3b8'
                };

                const apiData = result.data.reduce((acc, val, idx) => {
                    const label = result.labels[idx];
                    acc[label] = val;
                    return acc;
                }, {});

                const labels = [];
                const data = [];
                const bgColors = [];

                allSeverities.forEach(severity => {
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
                            borderColor: '#1e293b',
                            borderWidth: 3,
                            hoverBorderColor: '#f1f5f9',
                            hoverBorderWidth: 2
                        }]
                    },
                    options: {
                        maintainAspectRatio: false,
                        responsive: true,
                        resizeDelay: 200,
                        plugins: {
                            legend: {
                                position: 'right',
                                labels: {
                                    color: '#94a3b8',
                                    usePointStyle: true,
                                    padding: 12,
                                    boxWidth: 8,
                                    font: {
                                        size: 11
                                    }
                                }
                            },
                            tooltip: {
                                backgroundColor: '#1e293b',
                                titleColor: '#f1f5f9',
                                bodyColor: '#94a3b8',
                                borderColor: '#334155',
                                borderWidth: 1,
                                padding: 12,
                                cornerRadius: 8
                            }
                        },
                        cutout: '65%',
                        onResize: function (chart, size) {
                            if (chart.canvas.parentNode.clientHeight === 300) {
                                return;
                            }
                        }
                    }
                });
            }
        })
        .catch(error => console.error(error));
}

function loadLatestAlerts() {
    fetch('/api/alerts?limit=10')
        .then(response => response.json())
        .then(alerts => {
            if (Array.isArray(alerts)) {
                const tbody = document.getElementById('alerts-table-body');
                tbody.innerHTML = '';

                if (alerts.length === 0) {
                    tbody.innerHTML = '<tr><td colspan="4" class="text-center">Aucune alerte</td></tr>';
                    return;
                }

                alerts.forEach(alert => {
                    const row = document.createElement('tr');
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
        .catch(error => console.error(error));
}

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
                        <code>${item.source_ip}</code>
                        <span class="badge bg-danger rounded-pill">${item.count}</span>
                    `;
                    list.appendChild(li);
                });
            }
        })
        .catch(error => console.error(error));
}

function generateReport(format) {
    const btnId = `btn-report-${format}`;
    const btn = document.getElementById(btnId);
    const originalText = btn.innerHTML;

    btn.disabled = true;
    btn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Generation...';

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
                window.location.href = data.download_url;
            } else {
                alert('Erreur: ' + (data.error || 'Erreur inconnue'));
            }
        })
        .catch(error => {
            console.error(error);
            alert('Erreur lors de la communication avec le serveur');
        })
        .finally(() => {
            btn.disabled = false;
            btn.innerHTML = originalText;
        });
}

function refreshDashboard() {
    loadStats();
    loadAlertsChart();
    loadSeverityChart();
    loadLatestAlerts();
    loadTopIPs();
}

document.addEventListener('DOMContentLoaded', function () {
    refreshDashboard();
    setInterval(refreshDashboard, 5000);
});
