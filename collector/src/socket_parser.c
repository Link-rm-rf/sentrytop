#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <arpa/inet.h>
#include <unistd.h>

extern void find_pid_by_inode(unsigned int target_inode, char *out_process_name);

int main(void) {
    while (1) {
        FILE *fp = fopen("/proc/net/tcp", "r");
        if (!fp) return 1;
        char line[256];
        fgets(line, 256, fp);
        while (fgets(line, 256, fp)) {
            char rem_addr[64]; unsigned int inode; int state;
            if (sscanf(line, "%*d: %*s %63[0-9A-F]:%*X %X %*s %*s %*s %*s %*s %u", rem_addr, &state, &inode) == 3) {
                if (state == 0x01) {
                    unsigned int ip_hex; sscanf(rem_addr, "%X", &ip_hex);
                    struct in_addr addr; addr.s_addr = ip_hex;
                    char proc[256] = {0};
                    find_pid_by_inode(inode, proc);
                    printf("{\"r_ip\": \"%s\", \"process\": \"%s\"}\n", inet_ntoa(addr), proc);
                    fflush(stdout);
                }
            }
        }
        fclose(fp);
        sleep(1);
    }
    return 0;
}
