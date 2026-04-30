#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <arpa/inet.h>
#include <unistd.h>
#include <signal.h>
#include "logger.h"

extern void find_pid_by_inode(unsigned int target_inode, char *out_process_name, size_t max_len);
extern void json_escape(const char *input, char *output, size_t max_len);

static volatile int keep_running = 1;

void signal_handler(int sig) {
    LOG_I("Received signal %d, shutting down...", sig);
    keep_running = 0;
}

/*
 * scan_proc_net: Iterates through a /proc/net/[tcp|udp][6] file to discover active network endpoints.
 * 
 * Logic:
 * 1. Skips the header line of the /proc file.
 * 2. Parses the 4th (remote_address:port) and 10th (inode) fields.
 * 3. Handles both 8-char (IPv4) and 32-char (IPv6) hex address formats.
 * 4. Filters for 'ESTABLISHED' state (0x01) for TCP, or all entries for UDP (which is stateless in /proc).
 * 5. Escapes process names to ensure the resulting JSON telemetry is valid.
 */
void scan_proc_net(const char *path) {
    FILE *fp = fopen(path, "r");
    if (!fp) {
        LOG_E("Failed to open %s.", path);
        return;
    }

    char line[512];
    if (!fgets(line, sizeof(line), fp)) {
        fclose(fp);
        return;
    }

    while (fgets(line, sizeof(line), fp) && keep_running) {
        char rem_addr_str[64]; 
        unsigned int inode; 
        unsigned int state;
        unsigned int rem_port;

        // The format for both tcp/udp and tcp6/udp6 is similar, but the address length differs
        if (sscanf(line, "%*d: %*s %63[0-9A-F]:%X %X %*s %*s %*s %*s %*s %u", rem_addr_str, &rem_port, &state, &inode) == 4) {
            // TCP established = 0x01, UDP = usually 0x07 (CLOSE) or 0x01
            if (state == 0x01 || (strstr(path, "udp") != NULL)) {
                char addr_str[INET6_ADDRSTRLEN] = {0};
                size_t addr_len = strlen(rem_addr_str);

                if (addr_len == 8) { // IPv4
                    unsigned int ip_hex;
                    if (sscanf(rem_addr_str, "%X", &ip_hex) != 1) continue;
                    if (ip_hex == 0) continue;
                    struct in_addr addr; addr.s_addr = ip_hex;
                    inet_ntop(AF_INET, &addr, addr_str, sizeof(addr_str));
                } else if (addr_len == 32) { // IPv6
                    struct in6_addr addr6;
                    uint32_t *p = (uint32_t *)&addr6;
                    if (sscanf(rem_addr_str, "%08X%08X%08X%08X", &p[0], &p[1], &p[2], &p[3]) != 4) continue;
                    // Check if ::
                    if (p[0] == 0 && p[1] == 0 && p[2] == 0 && p[3] == 0) continue;
                    inet_ntop(AF_INET6, &addr6, addr_str, sizeof(addr_str));
                } else {
                    continue;
                }

                char proc[512] = {0};
                char escaped_proc[1024] = {0};

                find_pid_by_inode(inode, proc, sizeof(proc));
                json_escape(proc, escaped_proc, sizeof(escaped_proc));

                const char *proto = strstr(path, "tcp") ? "tcp" : "udp";
                printf("{\"r_ip\": \"%s\", \"r_port\": %u, \"proto\": \"%s\", \"process\": \"%s\"}\n", 
                       addr_str, rem_port, proto, escaped_proc);
                fflush(stdout);
            }
        }
    }
    fclose(fp);
}

int main(int argc, char *argv[]) {
    int polling_interval = 1;
    if (argc > 1) {
        polling_interval = atoi(argv[1]);
        if (polling_interval < 1) polling_interval = 1;
    }

    signal(SIGINT, signal_handler);
    signal(SIGTERM, signal_handler);

    LOG_I("SentryTop Collector v1.0.0 started with interval %ds.", polling_interval);

    while (keep_running) {
        scan_proc_net("/proc/net/tcp");
        scan_proc_net("/proc/net/udp");
        scan_proc_net("/proc/net/tcp6");
        scan_proc_net("/proc/net/udp6");
        if (keep_running) sleep(polling_interval);
    }

    LOG_I("SentryTop Collector stopped.");
    return 0;
}

