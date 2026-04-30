# Deployment Guide

SentryTop is designed to run as a persistent background service. This guide covers production deployment using systemd.

## Systemd Integration

We recommend running SentryTop as a systemd service to ensure it starts on boot and restarts automatically on failure.

### 1. Create the Service File

Create a file named `/etc/systemd/system/sentrytop.service` with the following content:

```ini
[Unit]
Description=SentryTop EDR Agent
After=network.target

[Service]
Type=simple
WorkingDirectory=/opt/sentrytop
# Running the collector as root is required for /proc/net and /proc/[pid]/fd access
ExecStart=/bin/bash -c "/opt/sentrytop/collector/sentry_collector 1 | /usr/bin/java -jar /opt/sentrytop/engine/target/sentry-engine-1.0.jar"
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

### 2. Enable and Start the Service

```bash
sudo systemctl daemon-reload
sudo systemctl enable sentrytop
sudo systemctl start sentrytop
```

## Production Best Practices

1.  **Least Privilege**: While the `sentry_collector` requires high privileges to scan `/proc`, the Java engine can be run as a separate user by splitting the pipeline.
2.  **Resource Limits**: Use systemd `MemoryMax` and `CPUQuota` to prevent SentryTop from consuming excessive system resources during high network traffic.
3.  **Logging**: Logs are directed to `journald`. Monitor them using:
    ```bash
    journalctl -u sentrytop -f
    ```

## Scaling Considerations

For high-throughput environments (e.g., core routers or busy web servers), increase the `polling_interval_ms` in `assets/config.json` to reduce CPU overhead from inode scanning.
