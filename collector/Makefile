CC = gcc
CFLAGS = -O3 -Wall -Wextra -Wpedantic -D_DEFAULT_SOURCE
TARGET = sentry_collector
SRCS = src/socket_parser.c src/proc_mapper.c src/logger.c src/json_utils.c

all: $(TARGET)
$(TARGET): $(SRCS)
	$(CC) $(CFLAGS) -o $(TARGET) $(SRCS)
clean:
	rm -f $(TARGET)
