# SENTRYTOP v1.1.0

A high-performance, professional-grade Linux EDR (Endpoint Detection and Response) terminal application. SentryTop provides real-time visibility into process behavior, network connections, and security threats with a retro-styled, production-hardened TUI.

![SentryTop UI](assets/ui_screenshot.png)

## Core Capabilities

* **Real-time Monitoring:** Live telemetry feed of security alerts (F1).
* **Process Management:** Interactive inspection and termination of suspicious processes with system protection (F2).
* **Network Insight:** Deep visibility into active connections with process correlation (F3).
* **Historical Audit:** Persistent alert logging via SQLite for post-incident analysis (F4).

## Architecture

SentryTop v1.1 follows a modular, thread-safe architecture:
* **C Collector:** Efficiently gathers raw system telemetry.
* **Java Engine:** Performs complex correlation and threat detection.
* **Python TUI:** A unified, non-blocking rendering engine built on the `blessed` library.

## Installation

Run the automated installer as root:

```bash
git clone https://github.com/Link-rm-rf/sentrytop.git
cd sentrytop
chmod +x install.sh
sudo ./install.sh
```

## Usage

```bash
sudo sentrytop
```

### Global Controls
* **`F1`**: Switch to Monitor Mode
* **`F2`**: Switch to Process Manager
* **`F3`**: Switch to Network Insight
* **`F4`**: Switch to Alert Logs
* **`Q`**: Quit Application

### Mode Specific Controls

#### [F1] Monitor
* **`P`**: Pause/Resume live feed
* **`C`**: Clear current feed

#### [F2] Process Manager
* **`J/K`** or **`↑/↓`**: Navigate process list
* **`K`**: Kill selected process (Requires confirmation)
* **`R`**: Refresh list

#### [F3] Network Insight
* **`J/K`** or **`↑/↓`**: Navigate connection list

#### [F4] Alert Logs
* **`J/K`** or **`↑/↓`**: Navigate logs

## Production Hardening (v1.1)

* **Thread Safety:** Implemented `threading.Lock` across all shared data structures (Database, StatsCache, AlertQueue).
* **Non-Blocking I/O:** Decoupled input handling and FIFO reading from the rendering loop.
* **Memory Safety:** Optimized data pipelines to maintain stable memory usage (<50MB).
* **UI Stability:** Fixed ASCII rendering truncation and screen buffer corruption ("TOR" bug).
* **System Protection:** Hardened process manager to prevent accidental termination of critical system services (sshd, systemd, etc.).

---
*SentryTop Security Engineering - 2026*
