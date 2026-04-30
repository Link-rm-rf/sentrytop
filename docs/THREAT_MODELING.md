# Threat Modeling & Detection Logic

SentryTop uses a multi-layered approach to detect unauthorized network activity.

## Detection Mechanisms

### 1. Threat Intel Matching (IP-based)
*   **Logic**: Every remote IP address discovered by the collector is checked against a localized `intel_db.json`.
*   **Trigger**: Exact match on a known malicious IP address.
*   **Fidelity**: High. This depends on the quality of your intelligence feed.

### 2. Suspicious Port Monitoring
*   **Logic**: SentryTop monitors for connections to ports commonly associated with reverse shells and C2 beacons (e.g., 4444, 1337).
*   **Trigger**: Any outbound connection to a port listed in `config.json`.
*   **Fidelity**: Medium. Legitimate applications may occasionally use these ports.

### 3. Behavioral Analysis (Beaconing)
*   **Logic**: The engine tracks the frequency of connections from a specific process to a specific destination.
*   **Trigger**: If the average interval between connections falls below a threshold (default 1s) over a window of 10 events, it is flagged as a potential beacon.
*   **Fidelity**: Medium-High. Useful for detecting automated reverse shells.

## Known Limitations

*   **Short-lived Connections**: If a connection is opened and closed between polling intervals, the collector may miss it.
*   **UDP State**: Unlike TCP, UDP is stateless in `/proc/net/udp`. SentryTop treats all entries in these files as active connections during the poll.
*   **Process Renaming**: Malicious processes that spoof their command line via `prctl` or `argv` manipulation may show misleading names.

## False Positives

Common causes of false positives include:
*   High-frequency legitimate API calls (triggers beaconing).
*   Dev tools or local services using "unusual" ports (e.g., 1337).
*   Shared hosting IPs appearing in threat feeds.
