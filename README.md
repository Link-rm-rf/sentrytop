# SentryTop v1.0.0

A lightweight Linux EDR agent for detecting beacons, reverse shells, and exfiltration.

![SentryTop UI](https://raw.githubusercontent.com/Link-rm-rf/sentrytop/main/assets/ui_screenshot.png)

## Installation

Run the automated installer as root:

```bash
git clone https://github.com/Link-rm-rf/sentrytop.git
cd sentrytop
chmod +x install.sh
sudo ./install.sh
```

## Usage

Launch the real-time monitoring interface:

```bash
sudo sentrytop
```

### Controls
* **`p`**: Pause/Resume the live feed.
* **`v`**: Toggle Verbose mode (hide/show safe connections).
* **`q`**: Exit the program.

---

## Why SentryTop?

SentryTop is built for security engineers who require zero-latency visibility without the overhead of cloud-tethered agents. It combines a high-speed C collector with a Java Virtual Thread correlator to provide actionable telemetry directly in the terminal.

### Feature Comparison

| Feature | SentryTop | Commercial EDRs | OSSEC / Wazuh |
| :--- | :--- | :--- | :--- |
| **Footprint** | **< 1.5% CPU, ~48MB RAM** | High (5-15% CPU) | Medium (2-5% CPU) |
| **Interface** | **Retro-styled TUI** | Web Dashboard | Web Dashboard |
| **Data Residency** | **100% Offline (Local)** | Cloud-tethered | Client-Server |
| **Setup Time** | **< 10 seconds** | Days/Weeks | Hours |

## Real-World Use Cases

* **Incident Response Triage:** Rapid visualization of anomalous outbound connections on compromised hosts.
* **Homelab Monitoring:** Lightweight alerting for personal servers and NAS devices.
* **Container Security:** Single-point monitoring of host and container network stacks.

## Architecture

```text
[ Kernel Space ]
      |
      v
[ /proc Filesystem ] <--- [ C Collector (Sensor) ]
      |                         |
      | (JSON Telemetry Stream) v
      |
[ Java Engine (Correlator) ] <--- [ Intel DB / Config ]
      |
      v
[ Python rich TUI (Renderer) ]
```

## Threat Detection Logic

1. **Intel Match:** Cross-references destination IPs against known C2 databases.
2. **Suspicious Ports:** Identifies outbound traffic on high-risk ports (e.g., 4444, 1337).
3. **Behavioral Analysis:** Detects beaconing patterns common in reverse shells.

---
*SentryTop Security Engineering*
