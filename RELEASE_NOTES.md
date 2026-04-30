# SentryTop v1.0.0 - The Open Source Linux EDR

We are thrilled to announce the v1.0.0 release of **SentryTop**, a lightweight, high-performance Endpoint Detection and Response (EDR) agent built from scratch for Linux.

SentryTop gives security analysts distraction-free, real-time visualization of endpoint threats and network connections directly within a terminal environment, utilizing a highly optimized C collector and a robust Java/Python correlator.

## 🚀 Key Features

* **High-Performance C Collector:** Direct `/proc` parsing with <1% CPU overhead.
* **Real-time Threat Correlation:** Detects reverse shells, beaconing, and anomalous process behavior.
* **Retro-Terminal UI:** Distraction-free, hacker-aesthetic CLI built in Python with rich.
* **Non-blocking Architecture:** Producer-consumer threading ensures the UI never stutters, even under heavy load.

## 📸 Interface

![SentryTop UI](https://raw.githubusercontent.com/Link-rm-rf/sentrytop/main/assets/ui_screenshot.png)

## 💻 Quick Start

Install SentryTop in seconds with our automated script:

```bash
curl -fsSL https://raw.githubusercontent.com/Link-rm-rf/sentrytop/main/install.sh | sudo bash
```

## 🔗 Documentation

* [Full README & Guide](https://github.com/Link-rm-rf/sentrytop#readme)
* [Technical Deep Dive Blog Post](https://github.com/Link-rm-rf/sentrytop/blob/main/docs/blog_post.md)
* [Contributing Guidelines](https://github.com/Link-rm-rf/sentrytop/blob/main/CONTRIBUTING.md)

---
*Built with passion by the SentryTop Security Engineering Team.*
