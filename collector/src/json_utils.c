#include <stdio.h>
#include <string.h>

void json_escape(const char *input, char *output, size_t max_len) {
    size_t j = 0;
    for (size_t i = 0; input[i] != '\0' && j < max_len - 1; i++) {
        switch (input[i]) {
            case '"':
                if (j + 2 < max_len) { output[j++] = '\\'; output[j++] = '"'; }
                break;
            case '\\':
                if (j + 2 < max_len) { output[j++] = '\\'; output[j++] = '\\'; }
                break;
            case '\b':
                if (j + 2 < max_len) { output[j++] = '\\'; output[j++] = 'b'; }
                break;
            case '\f':
                if (j + 2 < max_len) { output[j++] = '\\'; output[j++] = 'f'; }
                break;
            case '\n':
                if (j + 2 < max_len) { output[j++] = '\\'; output[j++] = 'n'; }
                break;
            case '\r':
                if (j + 2 < max_len) { output[j++] = '\\'; output[j++] = 'r'; }
                break;
            case '\t':
                if (j + 2 < max_len) { output[j++] = '\\'; output[j++] = 't'; }
                break;
            default:
                if (input[i] < 32) {
                    // Control characters
                    if (j + 6 < max_len) {
                        j += snprintf(&output[j], 7, "\\u%04x", input[i]);
                    }
                } else {
                    output[j++] = input[i];
                }
                break;
        }
    }
    output[j] = '\0';
}
