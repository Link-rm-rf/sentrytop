# SENTRYTOP v2.0.0 - Professional SOC/EDR Terminal

SENTRYTOP is an elite, professional-grade Linux EDR (Endpoint Detection and Response) platform designed for cinematic real-time threat hunting and incident response.

![SentryTop 2.0](assets/ui_screenshot.png)

## Architecture

SENTRYTOP 2.0 is powered by a **Unified Rust Agent**, replacing the legacy Java/Python stack.
* **Unified Brain:** Built in Rust for maximum performance and memory safety.
* **Async Engine:** Powered by `tokio` for zero-latency telemetry processing.
* **TUI Framework:** Highly responsive `ratatui` interface with high information density.
* **Persistence:** `SQLite` backend for historical incident auditing.

## Key Features

* **Advanced Threat Detection:** Behavioral heuristics, IOC matching, and resource anomaly detection.
* **Real-time Telemetry:** Deep visibility into process ancestry, network connections, and resource usage.
* **Stateful Investigation:** Persistent modules for monitoring, process management, and forensic logging.
* **Operational Aesthetic:** High-density, professional-grade TUI designed for SOC analysts.

## Global Controls

* **`F1`**: Dashboard / SOC Overview
* **`F2`**: Monitor (Live Threat Feed)
* **`F3`**: Process Manager
* **`F4`**: Network Insight
* **`F5`**: Historical Alert Logs
* **`Q`** or **`ESC`**: Secure Shutdown

## Build & Installation

### Prerequisites
* Rust & Cargo (1.75+)
* SQLite Development Libraries (`libsqlite3-dev`)

### Installation
```bash
# Clone the repository
git clone https://github.com/Link-rm-rf/sentrytop.git
cd sentrytop

# Build the professional agent
cd agent
cargo build --release

# Run the platform
sudo ./target/release/sentrytop-agent
```

---
*SentryTop Security Engineering - 2026*
