# API & Telemetry Reference

The SentryTop collector emits telemetry in JSON format via `stdout`. This stream is consumed by the Java engine.

## Telemetry Format

Each line is a self-contained JSON object:

```json
{
  "r_ip": "1.2.3.4",
  "r_port": 443,
  "proto": "tcp",
  "process": "/usr/bin/curl [Parent: bash(1234)]"
}
```

### Field Definitions

| Field | Type | Description |
| :--- | :--- | :--- |
| `r_ip` | String | Remote IP address (IPv4 or IPv6). |
| `r_port` | Integer | Remote port number. |
| `proto` | String | Network protocol (`tcp` or `udp`). |
| `process` | String | Full command line of the process, including parent info. |

## Internal Logic: Inode Mapping

The collector maps network sockets to processes by:
1.  Reading `/proc/net/[tcp|udp][6]`.
2.  Extracting the `inode` for established connections.
3.  Scanning `/proc/[pid]/fd/` for symlinks matching `socket:[<inode>]`.
4.  Resolving the `PID` to a command line via `/proc/[pid]/cmdline`.
5.  Traversing `/proc/[pid]/status` to find the Parent PID (PPID) and its name.
