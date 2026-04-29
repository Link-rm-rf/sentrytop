CC = gcc
CFLAGS = -O3 -Wall
TARGET = sentry_collector
SRCS = src/socket_parser.c src/proc_mapper.c

all: $(TARGET)
$(TARGET): $(SRCS)
	$(CC) $(CFLAGS) -o $(TARGET) $(SRCS)
clean:
	rm -f $(TARGET)
