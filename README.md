# LogMonitor

Linux log monitoring and security analysis tool.

## Features

- **Real-time & Batch Detection** - Analyze logs instantly (daemon) or retrospectively
- **Security Rules** - Brute force SSH, multiple accounts attack, root logins, sensitive file access, activity spikes
- **Web Dashboard** - Visualize alerts, statistics, and generate reports
- **PDF/CSV Reports** - Automated incident reports
- **SQLite Storage** - Local, privacy-focused database

## Quick Start

### Installation Système (Recommandé - Sans venv)

```bash
# Clone and install globally with pipx
git clone https://github.com/Lil-grxpe/LogMonitor.git
cd LogMonitor
./install_system.sh

# Use directly without venv activation
logmonitor scan -f /var/log/auth.log
logmonitor alerts list
logmonitor web --daemon
```

### Installation avec Environnement Virtuel

```bash
# Clone and install
git clone https://github.com/Lil-grxpe/LogMonitor.git
cd LogMonitor
./install.sh

# Activate venv first
source venv/bin/activate

# Then use logmonitor
logmonitor scan -f /var/log/auth.log
```

**Accès Dashboard**: http://localhost:5000  
**Identifiants par défaut**: admin / admin

## Usage

### CLI Commands

```bash
# Scan log file
logmonitor scan -f /path/to/logfile

# List alerts (filter by severity)
logmonitor alerts list --severity critical

# Generate reports
logmonitor report generate --format pdf
logmonitor report generate --format csv

# Clear database
logmonitor clean --force
```

### Daemon Mode

```bash
# Start background monitoring
logmonitor start

# Check status
logmonitor status

# Stop daemon
logmonitor stop
```

### Web Dashboard

```bash
# Foreground mode
logmonitor web --port 5000

# Background mode
logmonitor web --daemon
```

## Configuration

Edit `config/logmonitor.yaml`:

```yaml
logs:
  auto_detect: true  # Auto-detect based on Linux distro
  paths:
    - /var/log/auth.log  # Debian/Ubuntu
    # - /var/log/secure  # RHEL/CentOS
  mode: streaming

detection:
  bruteforce_ssh:
    enabled: true
    threshold: 5
    time_window: 300
```

## Supported Distributions

| Distribution | Log Paths |
|--------------|-----------|
| Debian/Ubuntu | /var/log/auth.log, /var/log/syslog |
| RHEL/CentOS/Fedora | /var/log/secure, /var/log/messages |
| Kali/Arch | journald (use export script) |

## Project Team

Academic project - ESGIS 2026

---
© 2026 LogMonitor Team
