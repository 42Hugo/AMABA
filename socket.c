#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <arpa/inet.h>
#include <fcntl.h>
#include <sys/select.h>
#include <errno.h>

#define PORT 12345
#define BUFFER_SIZE 1024

// Global variables for sockets
int server_fd, client_fd;
struct sockaddr_in address;
int addrlen = sizeof(address);
char buffer[BUFFER_SIZE] = {0};
int loop = 1;

/*fct for the sockets*/
void set_nonblocking(int fd) {
    int flags = fcntl(fd, F_GETFL, 0);
    if (flags < 0) {
        perror("fcntl(F_GETFL)");
        exit(EXIT_FAILURE);
    }
    if (fcntl(fd, F_SETFL, flags | O_NONBLOCK) < 0) {
        perror("fcntl(F_SETFL)");
        exit(EXIT_FAILURE);
    }
}

void start_socket() {
    int opt = 1;

    // Create socket file descriptor
    if ((server_fd = socket(AF_INET, SOCK_STREAM, 0)) == 0) {
        perror("socket failed");
        exit(EXIT_FAILURE);
    }

    // Set the socket options to allow reuse of the address
    if (setsockopt(server_fd, SOL_SOCKET, SO_REUSEADDR | SO_REUSEPORT, &opt, sizeof(opt))) {
        perror("setsockopt failed");
        close(server_fd);
        exit(EXIT_FAILURE);
    }

    // Bind the socket to the port
    address.sin_family = AF_INET;
    address.sin_addr.s_addr = INADDR_ANY;
    address.sin_port = htons(PORT);

    if (bind(server_fd, (struct sockaddr *)&address, sizeof(address)) < 0) {
        perror("bind failed");
        close(server_fd);
        exit(EXIT_FAILURE);
    }

    // Listen for incoming connections
    if (listen(server_fd, 3) < 0) {
        perror("listen");
        close(server_fd);
        exit(EXIT_FAILURE);
    }

    printf("Server listening on port %d\n", PORT);

    // Set the server socket to non-blocking mode
    set_nonblocking(server_fd);
}

void close_socket() {
    if (client_fd != -1) {
        close(client_fd);
    }
    close(server_fd);
}

void listen_to_socket() {
    if (client_fd == -1) {
        // No client connection yet, try to accept one
        client_fd = accept(server_fd, (struct sockaddr *)&address, (socklen_t*)&addrlen);
        if (client_fd < 0) {
            if (errno != EWOULDBLOCK) {
                perror("accept");
            }
            client_fd = -1;
        } else {
            printf("Client connected\n");
            set_nonblocking(client_fd);
        }
    } else {
        // Client connected, listen for data
        fd_set read_fds;
        struct timeval timeout;

        FD_ZERO(&read_fds);
        FD_SET(client_fd, &read_fds);

        timeout.tv_sec = 0;
        timeout.tv_usec = 0;  // No wait

        int activity = select(client_fd + 1, &read_fds, NULL, NULL, &timeout);

        if (activity < 0) {
            perror("select");
        } else if (activity > 0 && FD_ISSET(client_fd, &read_fds)) {
            // Read data from the client
            int bytes_read = read(client_fd, buffer, BUFFER_SIZE);
            if (bytes_read > 0) {
                buffer[bytes_read] = '\0'; // Null-terminate the received string
                printf("Received from client: %s\n", buffer);
                //strcpy(message, buffer);

                // Send a response back to the client
                char *response = "Hello from C server!";
                write(client_fd, response, strlen(response));

                if (strcmp(buffer, "0") == 0) {
                    loop = 0;
                }
            } else if (bytes_read == 0) {
                // Client disconnected
                printf("Client disconnected\n");
                close(client_fd);
                client_fd = -1;
            }
        }
    }
}


int main() {
    start_socket();

    while (loop) {
        listen_to_socket();
    }

    close_socket();
    printf("killing c process");
    return 0;
}
