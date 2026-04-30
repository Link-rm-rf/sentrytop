#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <dirent.h>
#include <unistd.h>
#include <ctype.h>
#include <errno.h>
#include <limits.h>
#include "logger.h"

/*
 * get_parent_info: Traverses /proc/[pid]/status to identify the Parent PID (PPID).
 * It then reads /proc/[ppid]/comm to get the executable name of the parent process.
 * This provides vital context for EDR (e.g., detecting a shell spawned by a web server).
 */
void get_parent_info(const char *pid, char *out_parent_info, size_t max_len) {
    char status_path[PATH_MAX];
    snprintf(status_path, sizeof(status_path), "/proc/%s/status", pid);
    FILE *fp = fopen(status_path, "r");
    if (!fp) return;

    char line[512];
    char ppid[16] = {0};
    while (fgets(line, sizeof(line), fp)) {
        if (strncmp(line, "PPid:", 5) == 0) {
            sscanf(line + 5, "%s", ppid);
            break;
        }
    }
    fclose(fp);

    if (strlen(ppid) > 0 && strcmp(ppid, "0") != 0) {
        char comm_path[PATH_MAX];
        snprintf(comm_path, sizeof(comm_path), "/proc/%s/comm", ppid);
        fp = fopen(comm_path, "r");
        if (fp) {
            char pcomm[256];
            if (fgets(pcomm, sizeof(pcomm), fp)) {
                pcomm[strcspn(pcomm, "\n")] = 0;
                snprintf(out_parent_info, max_len, "%s(%s)", pcomm, ppid);
            }
            fclose(fp);
        }
    }
}

/*
 * find_pid_by_inode: Performs a reverse lookup from a socket inode to a Process ID.
 * 
 * Logic:
 * 1. Iterates through all numeric directories in /proc (PIDs).
 * 2. Scans each /proc/[pid]/fd/ directory for symlinks.
 * 3. Readlink() each symlink to check if it points to "socket:[<target_inode>]".
 * 4. If found, resolves the full command line of the process.
 */
void find_pid_by_inode(unsigned int target_inode, char *out_process_name, size_t max_len) {
    DIR *proc_dir = opendir("/proc");
    if (!proc_dir) {
        LOG_E("Could not open /proc: %s", strerror(errno));
        snprintf(out_process_name, max_len, "ERROR_PROC_OPEN");
        return;
    }

    struct dirent *entry;
    while ((entry = readdir(proc_dir)) != NULL) {
        if (!isdigit(entry->d_name[0])) continue;

        char fd_path[PATH_MAX];
        snprintf(fd_path, sizeof(fd_path), "/proc/%s/fd", entry->d_name);
        
        DIR *fd_dir = opendir(fd_path);
        if (!fd_dir) {
            LOG_D("Could not open %s: %s", fd_path, strerror(errno));
            continue;
        }

        struct dirent *fd_entry;
        while ((fd_entry = readdir(fd_dir)) != NULL) {
            if (fd_entry->d_name[0] == '.') continue;

            char link_path[PATH_MAX + 256], target_path[PATH_MAX];
            snprintf(link_path, sizeof(link_path), "%s/%s", fd_path, fd_entry->d_name);
            
            ssize_t len = readlink(link_path, target_path, sizeof(target_path) - 1);
            if (len != -1) {
                target_path[len] = '\0';
                unsigned int inode;
                if (sscanf(target_path, "socket:[%u]", &inode) == 1 && inode == target_inode) {
                    char cmd_path[PATH_MAX];
                    snprintf(cmd_path, sizeof(cmd_path), "/proc/%s/cmdline", entry->d_name);
                    FILE *cmd_fp = fopen(cmd_path, "r");
                    if (cmd_fp) {
                        if (fgets(out_process_name, max_len, cmd_fp)) {
                            if (strlen(out_process_name) == 0) {
                                fclose(cmd_fp);
                                snprintf(cmd_path, sizeof(cmd_path), "/proc/%s/comm", entry->d_name);
                                cmd_fp = fopen(cmd_path, "r");
                                if (cmd_fp) {
                                    if (fgets(out_process_name, max_len, cmd_fp)) {
                                        out_process_name[strcspn(out_process_name, "\n")] = 0;
                                    }
                                }
                            }
                        }
                        if (cmd_fp) fclose(cmd_fp);
                        
                        if (strlen(out_process_name) == 0) {
                            snprintf(out_process_name, max_len, "UNKNOWN_EMPTY_CMD");
                        }

                        char parent_info[512] = {0};
                        get_parent_info(entry->d_name, parent_info, sizeof(parent_info));
                        if (strlen(parent_info) > 0) {
                            char temp[1024];
                            snprintf(temp, sizeof(temp), "%s [Parent: %s]", out_process_name, parent_info);
                            snprintf(out_process_name, max_len, "%s", temp);
                        }

                        closedir(fd_dir);
                        closedir(proc_dir);
                        return;
                    } else {
                        LOG_W("Found matching inode %u in PID %s but could not read cmdline: %s", 
                              target_inode, entry->d_name, strerror(errno));
                    }
                }
            }
        }
        closedir(fd_dir);
    }
    closedir(proc_dir);
    snprintf(out_process_name, max_len, "UNKNOWN");
}
