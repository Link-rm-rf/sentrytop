# Installation Guide

This guide provides step-by-step instructions for setting up SentryTop on various Linux distributions.

## Prerequisites

Before installing SentryTop, ensure your system meets the following requirements:
*   **Operating System**: Linux Kernel 5.0+ (requires `/proc` filesystem)
*   **Compiler**: `gcc` (build-essential)
*   **Java**: OpenJDK 21 or higher
*   **Build Tools**: Maven 3.x, Make

## Debian / Ubuntu (20.04+)

1.  Update your package list:
    ```bash
    sudo apt update
    ```
2.  Install required dependencies:
    ```bash
    sudo apt install -y build-essential gcc openjdk-21-jdk maven
    ```
3.  Clone and build the project:
    ```bash
    git clone https://github.com/link-rm-rf/sentrytop.git
    cd sentrytop
    ./scripts/setup.sh # Or follow manual build steps below
    ```

## RHEL / CentOS / Fedora (8+)

1.  Enable repositories and install dependencies:
    ```bash
    sudo dnf groupinstall "Development Tools"
    sudo dnf install -y java-21-openjdk-devel maven
    ```
2.  Clone and build the project:
    ```bash
    git clone https://github.com/link-rm-rf/sentrytop.git
    cd sentrytop
    make -C collector
    cd engine && mvn clean package -DskipTests
    ```

## Manual Build Steps

If you prefer to build components individually:

### 1. Build the Collector (C)
```bash
cd collector
make
```
This generates the `sentry_collector` binary.

### 2. Build the Engine (Java)
```bash
cd engine
mvn clean package -DskipTests
```
This generates `target/sentry-engine-1.0.jar`.

## Troubleshooting Installation

*   **Missing Java 21**: If your distro doesn't provide OpenJDK 21, use [SDKMAN!](https://sdkman.io/) or download it from [Adoptium](https://adoptium.net/).
*   **Permission Denied**: The collector requires access to `/proc/[pid]/fd`, which typically requires `sudo` or the `CAP_SYS_PTRACE` capability.
