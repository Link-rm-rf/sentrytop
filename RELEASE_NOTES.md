# SentryTop v1.0.0 Release Notes

We are proud to announce the first stable release of **SentryTop**, a standalone Linux EDR agent designed for real-time network threat detection and behavioral analysis.

## Key Features

*   **Real-time Network Monitoring**: Polls `/proc/net` to discover TCP/UDP connections for both IPv4 and IPv6.
*   **Process Attribution**: Automatically maps network sockets to the responsible process command line and its parent process.
*   **Multi-Layered Detection Engine**:
    *   **Intel Match**: High-fidelity matching against a local threat intelligence database.
    *   **Suspicious Port Detection**: Alerts on connections to high-risk ports (e.g., 4444, 1337).
    *   **Behavioral Beaconing**: Detects automated repetitive connection patterns via window-based frequency analysis.
*   **High Performance**:
    *   **C Collector**: Optimized for low CPU and memory overhead.
    *   **Java Correlator**: Utilizes Java 21 Virtual Threads (Project Loom) for massive concurrency with minimal RAM.
*   **Production Ready**: Includes systemd service integration, automated installation scripts, and periodic health metrics.

## Technical Improvements in 1.0.0

*   Full IPv6 support for TCP and UDP.
*   Strict compiler warnings resolved in the C collector.
*   Improved process name resolution with parent process context.
*   Periodic metrics reporting (Events, Alerts, Memory).
*   Standardized JSON telemetry format.

## Installation

```bash
git clone https://github.com/link-rm-rf/sentrytop.git
cd sentrytop
sudo ./scripts/install.sh
```

## Community & Support

SentryTop is open-source and built for the security community. Contributions, bug reports, and feedback are welcome!
