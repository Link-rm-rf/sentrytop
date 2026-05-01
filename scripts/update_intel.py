import requests
import json
import datetime
import os
import sys

# SentryTop Intel Update Script
# Fetches real threat feeds and merges them into intel_db.json

INTEL_DB_PATH = "sentrytop/assets/intel_db.json"

def fetch_urlhaus():
    """Fetch recent malware URLs/domains from URLhaus via direct download."""
    url = "https://urlhaus.abuse.ch/downloads/json_recent/"
    try:
        r = requests.get(url, timeout=30)
        if r.status_code == 200:
            data = r.json()
            if isinstance(data, list):
                return data
            if isinstance(data, dict):
                # If it's a dict, the values are the entries
                return list(data.values())
            return []
    except Exception as e:
        print(f"[!] Error fetching URLhaus: {e}")
    return []

def fetch_ipset(url):
    """Fetch an IP list from a raw URL (FireHOL style)."""
    try:
        r = requests.get(url, timeout=15)
        if r.status_code == 200:
            ips = []
            for line in r.text.splitlines():
                line = line.strip()
                if line and not line.startswith("#"):
                    ips.append(line)
            return ips
    except Exception as e:
        print(f"[!] Error fetching IPset from {url}: {e}")
    return []

def update():
    print("[*] Starting SentryTop Intel Update...")
    
    intel = {
        "malicious_ips": {},
        "malware_domains": {},
        "suspicious_ports": [4444, 1337, 6667, 8080, 9001, 5555, 7777],
        "last_updated": datetime.date.today().isoformat()
    }

    # 1. GreyNoise (Scanners/Noise) - Using IPsum as a high-quality proxy
    print("[*] Fetching GreyNoise/Malicious IPs (via IPsum)...")
    ipsum_ips = fetch_ipset("https://raw.githubusercontent.com/stamparm/ipsum/master/ipsum.txt")
    # IPSum format is: IP <score>. We only want high score ones (e.g. > 3)
    count = 0
    for line in ipsum_ips:
        parts = line.split()
        if len(parts) >= 2:
            ip = parts[0]
            score = int(parts[1])
            if score >= 3: # Reasonable threshold for maliciousness
                intel["malicious_ips"][ip] = {
                    "threat": "Known Malicious",
                    "confidence": min(0.99, 0.5 + (score * 0.1)),
                    "family": "Unknown"
                }
                count += 1
                if count >= 500: break # Requirement was ~500

    # 2. Botnet C2 (Feodo Tracker)
    print("[*] Fetching Botnet C2 data (Feodo)...")
    feodo_ips = fetch_ipset("https://raw.githubusercontent.com/firehol/blocklist-ipsets/master/feodo.ipset")
    for ip in feodo_ips:
        if ip not in intel["malicious_ips"]:
            intel["malicious_ips"][ip] = {
                "threat": "Botnet C2",
                "confidence": 0.95,
                "family": "Feodo"
            }

    # 3. URLhaus (Malicious Domains & IPs)
    print("[*] Fetching URLhaus data...")
    urlhaus_data = fetch_urlhaus()
    # Limit URLhaus to ~1000 entries to keep DB small
    processed = 0
    for item in urlhaus_data:
        # Each item might be a list of dicts (based on inspection)
        entries = item if isinstance(item, list) else [item]
        for entry in entries:
            if not isinstance(entry, dict): continue
            
            host = entry.get('host')
            # If 'host' is missing, try to parse from 'url'
            if not host and 'url' in entry:
                from urllib.parse import urlparse
                host = urlparse(entry['url']).hostname
            
            threat = entry.get('threat', 'Malware')
            if host:
                is_ip = True
                try:
                    import socket
                    socket.inet_aton(host)
                except:
                    is_ip = False
                
                if is_ip:
                    if host not in intel["malicious_ips"]:
                        intel["malicious_ips"][host] = {
                            "threat": threat,
                            "confidence": 0.95,
                            "family": "Unknown"
                        }
                else:
                    if host not in intel["malware_domains"]:
                        intel["malware_domains"][host] = {
                            "threat": threat,
                            "confidence": 0.92
                        }
            processed += 1
            if processed >= 1000: break
        if processed >= 1000: break

    # Ensure assets directory exists
    os.makedirs(os.path.dirname(INTEL_DB_PATH), exist_ok=True)

    with open(INTEL_DB_PATH, "w") as f:
        json.dump(intel, f, indent=2)
    
    print(f"[+] Update complete! Saved to {INTEL_DB_PATH}")
    print(f"    - IPs: {len(intel['malicious_ips'])}")
    print(f"    - Domains: {len(intel['malware_domains'])}")

if __name__ == "__main__":
    update()
