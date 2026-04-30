#ifndef LOGGER_H
#define LOGGER_H

typedef enum {
    LOG_DEBUG,
    LOG_INFO,
    LOG_WARN,
    LOG_ERROR
} log_level_t;

void log_msg(log_level_t level, const char *fmt, ...);
void set_log_level(log_level_t level);

#define LOG_D(fmt, ...) log_msg(LOG_DEBUG, fmt, ##__VA_ARGS__)
#define LOG_I(fmt, ...) log_msg(LOG_INFO, fmt, ##__VA_ARGS__)
#define LOG_W(fmt, ...) log_msg(LOG_WARN, fmt, ##__VA_ARGS__)
#define LOG_E(fmt, ...) log_msg(LOG_ERROR, fmt, ##__VA_ARGS__)

#endif
