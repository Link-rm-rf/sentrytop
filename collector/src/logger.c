#include "logger.h"
#include <stdio.h>
#include <stdarg.h>
#include <time.h>

static log_level_t current_level = LOG_INFO;

void set_log_level(log_level_t level) {
    current_level = level;
}

void log_msg(log_level_t level, const char *fmt, ...) {
    if (level < current_level) return;

    const char *level_str[] = {"DEBUG", "INFO", "WARN", "ERROR"};
    time_t now = time(NULL);
    struct tm *t = localtime(&now);
    char time_buf[64];
    strftime(time_buf, sizeof(time_buf), "%Y-%m-%d %H:%M:%S", t);

    // Write logs to stderr so they don't interfere with the JSON pipe
    fprintf(stderr, "[%s] [%s] ", time_buf, level_str[level]);

    va_list args;
    va_start(args, fmt);
    vfprintf(stderr, fmt, args);
    va_end(args);

    fprintf(stderr, "\n");
}
