# SentryTop Roadmap

SentryTop v1.0.0 is the foundation: a lightweight, read-only EDR agent focused on high-performance telemetry extraction and visualization. 

Our vision for **v2.0** and beyond is to transform SentryTop from a detection engine into an active, enterprise-ready mitigation platform.

## Q3 2026: Active Mitigation & Control (v1.5)
- **Active Mitigation Engine:** Introduce a rule-based execution engine that allows SentryTop to automatically issue `kill -9` or drop packets (via `iptables`/`nftables` integration) when high-confidence alerts are triggered.
- **Custom Yara/Sigma Rules:** Move away from hardcoded Java logic and allow users to supply standard `.yara` or Sigma files for behavioral matching.
- **REST API & Webhooks:** Add a lightweight HTTP server to the Java correlator to push alerts to Slack, PagerDuty, or Splunk.

## Q4 2026: Cloud Native & Scaling (v2.0)
- **Kubernetes Native:** Provide official Helm charts and DaemonSet configurations to deploy SentryTop across K8s clusters, mapping PIDs back to Pod Names and Namespaces.
- **eBPF Sensor Backend:** While `/proc` parsing is highly compatible, eBPF allows for sub-millisecond network tracing. We will introduce an optional eBPF sensor module for modern kernels (5.x+) to capture extremely short-lived connection spikes.
- **Centralized Dashboard (Optional):** We love the terminal, but managing 500 agents requires a central view. We will release an optional aggregator backend to pull metrics from fleet deployments.

## Q1 2027: Advanced Threat Intel
- **Live Threat Feed Integration:** Direct ingestion of MISP/STIX formats.
- **Machine Learning Baselines:** A small local model to baseline "normal" network traffic and alert on standard deviation anomalies without needing fixed signatures.
