# SentryTop

SentryTop is a standalone kernel-polling Linux EDR agent designed to detect active beacons, reverse shells, and unauthorized data exfiltration.

This is a functional security tool that monitors the live state of the Linux networking stack via the /proc filesystem.

---

### **Detection Example**

![SentryTop Terminal Output](assets/demo.png)

*A standard `nc` beacon reaching out to a known malicious IP (45.33.32.156) is flagged in real-time, while standard system connections are validated and passed.*

---

## Architecture
* **Sensor (C):** A high-performance collector that polls /proc/net/tcp and maps socket inodes via /proc/[pid]/fd [cite: 49-67].
* **Correlator (Java 21):** A virtual-thread powered correlation engine that ingests JSON telemetry and evaluates threats against a localized database [cite: 173-185].

## Build Requirements
Tested on Debian/Ubuntu and WSL2.
`sudo apt update && sudo apt install -y build-essential gcc openjdk-21-jdk maven`

## Installation & Usage
1. Clone the repository:
   `git clone https://github.com/link-rm-rf/sentrytop.git`
2. Enter the directory:
   `cd sentrytop`
3. Run the pipeline (Requires sudo for the C sensor):
   `./scripts/sentrytop`

## Security & Performance
* **Zero Cloud Dependency:** Operates entirely offline for maximum privacy.
* **Minimal Overhead:** Optimized C collector and Java Loom virtual threads ensure near real-time processing [cite: 121-123].
* **Least Privilege:** Sensor runs as ROOT while the engine runs as USER[cite: 120].
