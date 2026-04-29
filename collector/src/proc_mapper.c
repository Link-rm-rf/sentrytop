#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <dirent.h>
#include <unistd.h>
#include <ctype.h>

void find_pid_by_inode(unsigned int target_inode, char *out_process_name) {
    DIR *proc_dir = opendir("/proc");
    if (!proc_dir) return;
    struct dirent *entry;
    while ((entry = readdir(proc_dir)) != NULL) {
        if (!isdigit(entry->d_name[0])) continue;
        char fd_path[4096];
        snprintf(fd_path, sizeof(fd_path), "/proc/%s/fd", entry->d_name);
        DIR *fd_dir = opendir(fd_path);
        if (!fd_dir) continue;
        struct dirent *fd_entry;
        while ((fd_entry = readdir(fd_dir)) != NULL) {
            char link_path[4096], target_path[4096];
            snprintf(link_path, sizeof(link_path), "%s/%s", fd_path, fd_entry->d_name);
            ssize_t len = readlink(link_path, target_path, sizeof(target_path) - 1);
            if (len != -1) {
                target_path[len] = '\0';
                unsigned int inode;
                if (sscanf(target_path, "socket:[%u]", &inode) == 1 && inode == target_inode) {
                    char cmd_path[4096];
                    snprintf(cmd_path, sizeof(cmd_path), "/proc/%s/cmdline", entry->d_name);
                    FILE *cmd_fp = fopen(cmd_path, "r");
                    if (cmd_fp) {
                        fgets(out_process_name, 256, cmd_fp);
                        fclose(cmd_fp);
                        closedir(fd_dir); closedir(proc_dir);
                        return;
                    }
                }
            }
        }
        closedir(fd_dir);
    }
    closedir(proc_dir);
    strcpy(out_process_name, "UNKNOWN");
}
