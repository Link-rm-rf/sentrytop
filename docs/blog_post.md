# I Built a Linux EDR Agent from Scratch—Here's What I Learned

Endpoint Detection and Response (EDR) tools are often viewed as black boxes—complex, proprietary, and heavy on system resources. As a security engineer, I wanted to demystify this. I set out to build a lightweight, open-source Linux EDR agent that I could trust, modify, and actually enjoy looking at. 

The result is **SentryTop**: a blazing-fast C-based collector paired with a Java correlator and a retro-styled Python terminal UI.

Here's a breakdown of how it works, the technical decisions I made along the way, and what I learned about Linux kernel internals.

---

## 1. The Problem Statement

Commercial EDRs suffer from a few common issues:
* **Resource Bloat:** Running heavy agents that consume 10-15% of the CPU just sitting idle.
* **Opaque Telemetry:** Analysts are given pre-chewed alerts, but lack the raw visibility into *why* a connection was flagged.
* **Clunky Web UIs:** Having to click through 5 pages of a web dashboard just to see the parent PID of a suspicious network connection.

I wanted something different: A tool that lived entirely in the terminal, gave me raw visibility with zero latency, and used less than 1% of my CPU.

## 2. Architecture Overview

SentryTop is built on a split-brain architecture:

1. **The Collector (C):** A high-speed polling engine that runs as root. It parses `/proc` to map open file descriptors, network sockets, and process trees.
2. **The Correlator (Java):** A multi-threaded analysis engine (leveraging Java Virtual Threads / Project Loom) that ingests the raw telemetry and cross-references it against threat intelligence and behavioral rules.
3. **The UI (Python):** A terminal user interface built with the `rich` library that asynchronously reads the correlator's stdout and renders a retro-hacker aesthetic without blocking the main event loop.

## 3. Key Technical Decisions

### Why Parse `/proc` instead of using eBPF?
While eBPF is the modern standard for Linux observability, it requires recent kernels and often introduces compilation complexities (BTF, kernel headers). By directly parsing `/proc/net/tcp`, `/proc/[pid]/fd`, and `/proc/[pid]/stat`, I was able to achieve a highly compatible, statically compiled collector that works on almost any Linux distribution from the last decade.

### Why Java Virtual Threads (Project Loom)?
The correlator needs to handle thousands of events per second without choking. Traditional OS threads are too heavy for 1:1 event mapping. By using Java 21's Virtual Threads, the engine can spawn a new lightweight thread for every incoming log line, independently resolving DNS or checking IP reputation without blocking the main ingestion pipeline.

### Why a Python TUI?
Security tools should be a joy to use. Python's `rich` and `psutil` libraries made it incredibly easy to build a resilient, beautiful terminal UI with asynchronous producer-consumer queues. It gives that "Hollywood Hacker" feel while providing dense, actionable data.

## 4. Threat Detection Logic

SentryTop doesn't just log connections; it correlates them. The detection logic focuses on:
* **Process Lineage Anomalies:** If `nginx` spawns `/tmp/.hidden_shell`, SentryTop flags it instantly.
* **Beaconing Behavior:** Connections to unknown external IPs that repeat at regular intervals are highlighted.
* **Port Mismatches:** If a process named `sshd` is communicating over port `4444`, it triggers a critical alert.

## 5. Performance Benchmarks

I rigorously tested SentryTop on an AWS `t3.micro` instance:
* **CPU Usage:** < 1.2% under load (polling 10 times a second).
* **Memory Footprint:** ~45MB for the Java Correlator, ~3MB for the C collector.
* **UI Latency:** < 100ms from process creation to UI render.

## 6. Lessons Learned

* **String manipulation in C is painful but worth it.** Writing safe, buffer-overflow-resistant C code for parsing `/proc` took time, but the performance gains over a Python or Go collector were undeniable.
* **Terminal UIs are hard.** Handling window resizes, ANSI escape codes, and non-blocking `stdin` in Python required careful thread management and terminal state restoration to avoid leaving the user's shell in a corrupted state upon exit.

## 7. How to Use It

I've open-sourced the entire project. You can install it on any Linux machine with a single command:

```bash
curl -fsSL https://raw.githubusercontent.com/Link-rm-rf/sentrytop/main/install.sh | sudo bash
```

Then, just run `sudo sentrytop`.

Check out the code on [GitHub](https://github.com/Link-rm-rf/sentrytop) and let me know what you think!
