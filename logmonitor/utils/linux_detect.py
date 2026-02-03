"""Linux distribution detection and log path configuration."""

import os
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Tuple


DISTRO_LOG_PATHS = {
    'debian': {
        'auth': ['/var/log/auth.log'],
        'syslog': ['/var/log/syslog'],
        'description': 'Debian/Ubuntu/Mint'
    },
    'ubuntu': {
        'auth': ['/var/log/auth.log'],
        'syslog': ['/var/log/syslog'],
        'description': 'Ubuntu'
    },
    'kali': {
        'auth': [],
        'syslog': [],
        'use_journald': True,
        'description': 'Kali Linux (uses journald)'
    },
    'rhel': {
        'auth': ['/var/log/secure'],
        'syslog': ['/var/log/messages'],
        'description': 'RHEL/CentOS/Fedora'
    },
    'centos': {
        'auth': ['/var/log/secure'],
        'syslog': ['/var/log/messages'],
        'description': 'CentOS'
    },
    'fedora': {
        'auth': ['/var/log/secure'],
        'syslog': ['/var/log/messages'],
        'description': 'Fedora'
    },
    'arch': {
        'auth': [],
        'syslog': [],
        'use_journald': True,
        'description': 'Arch Linux (uses journald)'
    },
    'opensuse': {
        'auth': ['/var/log/secure'],
        'syslog': ['/var/log/messages'],
        'description': 'openSUSE'
    },
    'alpine': {
        'auth': ['/var/log/messages'],
        'syslog': ['/var/log/messages'],
        'description': 'Alpine Linux'
    }
}


def detect_distro() -> str:
    """
    Detect the current Linux distribution.
    
    Returns:
        Distribution identifier (debian, ubuntu, rhel, etc.) or 'unknown'
    """
    os_release = Path('/etc/os-release')
    
    if os_release.exists():
        content = os_release.read_text().lower()
        
        if 'kali' in content:
            return 'kali'
        elif 'ubuntu' in content:
            return 'ubuntu'
        elif 'debian' in content:
            return 'debian'
        elif 'fedora' in content:
            return 'fedora'
        elif 'centos' in content:
            return 'centos'
        elif 'red hat' in content or 'rhel' in content:
            return 'rhel'
        elif 'arch' in content:
            return 'arch'
        elif 'opensuse' in content or 'suse' in content:
            return 'opensuse'
        elif 'alpine' in content:
            return 'alpine'
    
    if Path('/etc/debian_version').exists():
        return 'debian'
    elif Path('/etc/redhat-release').exists():
        return 'rhel'
    elif Path('/etc/arch-release').exists():
        return 'arch'
    
    return 'unknown'


def get_log_paths(distro: Optional[str] = None) -> Dict[str, any]:
    """
    Get log file paths for the specified or detected distribution.
    
    Args:
        distro: Distribution name (auto-detected if None)
    
    Returns:
        Dictionary with 'auth', 'syslog' paths and metadata
    """
    if distro is None:
        distro = detect_distro()
    
    if distro in DISTRO_LOG_PATHS:
        return DISTRO_LOG_PATHS[distro].copy()
    
    return {
        'auth': ['/var/log/auth.log', '/var/log/secure'],
        'syslog': ['/var/log/syslog', '/var/log/messages'],
        'description': 'Unknown (trying common paths)'
    }


def find_existing_log_paths(distro: Optional[str] = None) -> List[str]:
    """
    Find log paths that actually exist on the current system.
    
    Args:
        distro: Distribution name (auto-detected if None)
    
    Returns:
        List of existing, readable log file paths
    """
    paths = get_log_paths(distro)
    existing = []
    
    for log_type in ['auth', 'syslog']:
        for path in paths.get(log_type, []):
            p = Path(path)
            if p.exists() and os.access(p, os.R_OK):
                existing.append(str(p))
    
    return existing


def uses_journald(distro: Optional[str] = None) -> bool:
    """
    Check if the distribution primarily uses journald.
    
    Args:
        distro: Distribution name (auto-detected if None)
    
    Returns:
        True if journald is the primary log system
    """
    if distro is None:
        distro = detect_distro()
    
    paths = DISTRO_LOG_PATHS.get(distro, {})
    return paths.get('use_journald', False)


def export_journald_logs(output_path: str, since: str = "24 hours ago") -> bool:
    """
    Export journald logs to a file for analysis.
    
    Args:
        output_path: Path to write exported logs
        since: Time period (journalctl format)
    
    Returns:
        True if export succeeded
    """
    try:
        result = subprocess.run(
            ['journalctl', '--since', since, '--no-pager'],
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if result.returncode == 0:
            Path(output_path).write_text(result.stdout)
            return True
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    
    return False


def auto_detect_log_paths() -> Tuple[str, List[str]]:
    """
    Auto-detect distribution and return available log paths.
    
    Returns:
        Tuple of (distro_name, list_of_log_paths)
    """
    distro = detect_distro()
    paths = find_existing_log_paths(distro)
    
    return distro, paths


if __name__ == '__main__':
    distro = detect_distro()
    print(f"Distribution: {distro}")
    print(f"Log paths: {get_log_paths(distro)}")
    print(f"Existing paths: {find_existing_log_paths(distro)}")
    print(f"Uses journald: {uses_journald(distro)}")
