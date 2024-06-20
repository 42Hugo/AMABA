/*****************************************************************************
 *
 *  $Id$
 *
 *  Copyright (C) 2007-2009  Florian Pose, Ingenieurgemeinschaft IgH
 *
 *  This file is part of the IgH EtherCAT Master.
 *
 *  The IgH EtherCAT Master is free software; you can redistribute it and/or
 *  modify it under the terms of the GNU General Public License version 2, as
 *  published by the Free Software Foundation.
 *
 *  The IgH EtherCAT Master is distributed in the hope that it will be useful,
 *  but WITHOUT ANY WARRANTY; without even the implied warranty of
 *  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General
 *  Public License for more details.
 *
 *  You should have received a copy of the GNU General Public License along
 *  with the IgH EtherCAT Master; if not, write to the Free Software
 *  Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
 *
 *  ---
 *
 *  The license mentioned above concerns the source code only. Using the
 *  EtherCAT technology and brand is only permitted in compliance with the
 *  industrial property and similar rights of Beckhoff Automation GmbH.
 *
 ****************************************************************************/

#include <errno.h>
#include <signal.h>
#include <stdio.h>
#include <string.h>
#include <sys/resource.h>
#include <sys/time.h>
#include <sys/types.h>
#include <unistd.h>
#include <time.h> /* clock_gettime() */
#include <sys/mman.h> /* mlockall() */
#include <sched.h> /* sched_setscheduler() */

//for the multi process with socket
#include <stdlib.h>
#include <arpa/inet.h>
#include <fcntl.h>
#include <sys/select.h>

/****************************************************************************/

#include "ecrt.h"

/****************************************************************************/

/** Task period in ns. */
#define PERIOD_NS   (100000000)

#define MAX_SAFE_STACK (8 * 1024) /* The maximum stack size which is
                                     guranteed safe to access without
                                     faulting */

/****************************************************************************/

/* Constants */
#define NSEC_PER_SEC (1000000000)
#define FREQUENCY (NSEC_PER_SEC / PERIOD_NS)

//socket var
#define PORT 12345
#define BUFFER_SIZE 10//9 bit + /n

int server_fd, client_fd;
struct sockaddr_in address;
int addrlen = sizeof(address);
char buffer[BUFFER_SIZE] = {0};
/****************************************************************************/

// EtherCAT
static ec_master_t *master = NULL;
static ec_master_state_t master_state = {};

static ec_domain_t *domain1 = NULL;
static ec_domain_state_t domain1_state = {};

static ec_slave_config_t *sc_ana_in = NULL;
static ec_slave_config_state_t sc_ana_in_state = {};

/****************************************************************************/

// process data
static uint8_t *domain1_pd = NULL;

#define BusCouplerPos  0, 0
#define DigOutSlavePos 0, 1
#define AnaOutSlavePos 0, 2
#define AnaInSlavePos  0, 3

#define Beckhoff_EK1100 0x00000002, 0x044c2c52
#define Beckhoff_EL2024 0x00000002, 0x07e83052
#define Beckhoff_EL4104 0x00000002, 0x10083052
#define Beckhoff_EL3164 0x00000002, 0x0c5c3052


// offsets for PDO entries
static unsigned int off_ana_in1;
static unsigned int off_ana_in2;
static unsigned int off_ana_out1;
static unsigned int off_ana_out2;
static unsigned int off_dig_out1;
//static unsigned int off_dig_out2;

const static ec_pdo_entry_reg_t domain1_regs[] = {
    {AnaInSlavePos,  Beckhoff_EL3164, 0x6000, 0x11, &off_ana_in1},
    {AnaInSlavePos,  Beckhoff_EL3164, 0x6010, 0x11, &off_ana_in2},
    {AnaOutSlavePos, Beckhoff_EL4104, 0x7000, 0x01, &off_ana_out1},
    {AnaOutSlavePos, Beckhoff_EL4104, 0x7010, 0x01, &off_ana_out2},
    {DigOutSlavePos, Beckhoff_EL2024, 0x7000, 0x01, &off_dig_out1},
    //{DigOutSlavePos, Beckhoff_EL2024, 0x7010, 0x01, &off_dig_out2},
    {}
};

static unsigned int counter = 0;
static unsigned int blink = 0;
static unsigned int dig1=0;
static unsigned int dig2=0;
static unsigned int dig3=0;
static float ana1=0.0f;
static float ana2=0.0f;
static unsigned int state= 1;//starts at 1 because the code is running
static unsigned int loop= 1;//loop until we get a state =0
//to test independently for the moment
static char message[] ="10000000";//message from the GUI to ethercat bit 1: on/off; bit2,3: dig out; bit4,5 and 6,7: pressure in bar^-1

/*****************************************************************************/

// Analog in --------------------------

static ec_pdo_entry_info_t slave_3_pdo_entries[] = {
    {0x6000, 0x01, 1}, /* Underrange */
    {0x6000, 0x02, 1}, /* Overrange */
    {0x6000, 0x03, 2}, /* Limit 1 */
    {0x6000, 0x05, 2}, /* Limit 2 */
    {0x6000, 0x07, 1}, /* Error */
    {0x0000, 0x00, 1}, /* Gap */
    {0x0000, 0x00, 5}, /* Gap */
    {0x6000, 0x0e, 1}, /* Sync error */
    {0x6000, 0x0f, 1}, /* TxPDO State */
    {0x6000, 0x10, 1}, /* TxPDO Toggle */
    {0x6000, 0x11, 16}, /* Value */
    {0x6010, 0x01, 1}, /* Underrange */
    {0x6010, 0x02, 1}, /* Overrange */
    {0x6010, 0x03, 2}, /* Limit 1 */
    {0x6010, 0x05, 2}, /* Limit 2 */
    {0x6010, 0x07, 1}, /* Error */
    {0x0000, 0x00, 1}, /* Gap */
    {0x0000, 0x00, 5}, /* Gap */
    {0x6010, 0x0e, 1}, /* Sync error */
    {0x6010, 0x0f, 1}, /* TxPDO State */
    {0x6010, 0x10, 1}, /* TxPDO Toggle */
    {0x6010, 0x11, 16}, /* Value */
    {0x6020, 0x01, 1}, /* Underrange */
    {0x6020, 0x02, 1}, /* Overrange */
    {0x6020, 0x03, 2}, /* Limit 1 */
    {0x6020, 0x05, 2}, /* Limit 2 */
    {0x6020, 0x07, 1}, /* Error */
    {0x0000, 0x00, 1}, /* Gap */
    {0x0000, 0x00, 5}, /* Gap */
    {0x6020, 0x0e, 1}, /* Sync error */
    {0x6020, 0x0f, 1}, /* TxPDO State */
    {0x6020, 0x10, 1}, /* TxPDO Toggle */
    {0x6020, 0x11, 16}, /* Value */
    {0x6030, 0x01, 1}, /* Underrange */
    {0x6030, 0x02, 1}, /* Overrange */
    {0x6030, 0x03, 2}, /* Limit 1 */
    {0x6030, 0x05, 2}, /* Limit 2 */
    {0x6030, 0x07, 1}, /* Error */
    {0x0000, 0x00, 1}, /* Gap */
    {0x0000, 0x00, 5}, /* Gap */
    {0x6030, 0x0e, 1}, /* Sync error */
    {0x6030, 0x0f, 1}, /* TxPDO State */
    {0x6030, 0x10, 1}, /* TxPDO Toggle */
    {0x6030, 0x11, 16}, /* Value */
};

static ec_pdo_info_t slave_3_pdos[] = {
    {0x1a00, 11, slave_3_pdo_entries + 0}, /* AI TxPDO-Map Standard Ch.1 */
    {0x1a02, 11, slave_3_pdo_entries + 11}, /* AI TxPDO-Map Standard Ch.2 */
    {0x1a04, 11, slave_3_pdo_entries + 22}, /* AI TxPDO-Map Standard Ch.3 */
    {0x1a06, 11, slave_3_pdo_entries + 33}, /* AI TxPDO-Map Standard Ch.4 */
};

static ec_sync_info_t slave_3_syncs[] = {
    {0, EC_DIR_OUTPUT, 0, NULL, EC_WD_DISABLE},
    {1, EC_DIR_INPUT, 0, NULL, EC_WD_DISABLE},
    {2, EC_DIR_OUTPUT, 0, NULL, EC_WD_DISABLE},
    {3, EC_DIR_INPUT, 4, slave_3_pdos + 0, EC_WD_DISABLE},
    {0xff}
};

// Analog out -------------------------

static ec_pdo_entry_info_t slave_2_pdo_entries[] = {
    {0x7000, 0x01, 16}, /* Analog output */
    {0x7010, 0x01, 16}, /* Analog output */
    {0x7020, 0x01, 16}, /* Analog output */
    {0x7030, 0x01, 16}, /* Analog output */
};

static ec_pdo_info_t slave_2_pdos[] = {
    {0x1600, 1, slave_2_pdo_entries + 0}, /* AO RxPDO-Map OutputsCh.1 */
    {0x1601, 1, slave_2_pdo_entries + 1}, /* AO RxPDO-Map OutputsCh.2 */
    {0x1602, 1, slave_2_pdo_entries + 2}, /* AO RxPDO-Map OutputsCh.3 */
    {0x1603, 1, slave_2_pdo_entries + 3}, /* AO RxPDO-Map OutputsCh.4 */
};

static ec_sync_info_t slave_2_syncs[] = {
    {0, EC_DIR_OUTPUT, 0, NULL, EC_WD_DISABLE},
    {1, EC_DIR_INPUT, 0, NULL, EC_WD_DISABLE},
    {2, EC_DIR_OUTPUT, 4, slave_2_pdos + 0, EC_WD_DISABLE},
    {3, EC_DIR_INPUT, 0, NULL, EC_WD_DISABLE},
    {0xff}
};

// Digital out ------------------------

static ec_pdo_entry_info_t slave_1_pdo_entries[] = {
    {0x7000, 0x01, 1}, /* Output */
    {0x7010, 0x01, 1}, /* Output */
    {0x7020, 0x01, 1}, /* Output */
    {0x7030, 0x01, 1}, /* Output */
};

static ec_pdo_info_t slave_1_pdos[] = {
    {0x1600, 1, slave_1_pdo_entries + 0}, /* Channel 1 */
    {0x1601, 1, slave_1_pdo_entries + 1}, /* Channel 2 */
    {0x1602, 1, slave_1_pdo_entries + 2}, /* Channel 3 */
    {0x1603, 1, slave_1_pdo_entries + 3}, /* Channel 4 */
};

static ec_sync_info_t slave_1_syncs[] = {
    {0, EC_DIR_OUTPUT, 4, slave_1_pdos + 0, EC_WD_ENABLE},
    {0xff}
};

/*****************************************************************************/

void decodeMessage(const char *mes)
{
    state=mes[0]-'0';
    dig1=mes[1]-'0';
    dig2=mes[2]-'0';
    dig3=mes[3]-'0';
    ana1 = (mes[4] - '0') * 10 + (mes[5] - '0');
    ana1 = (ana1 / 20.0f) * 65535.0f;
    ana2 = (mes[6] - '0') * 10 + (mes[7] - '0');
    ana2 = (ana2 / 20.0f) * 65535.0f;
}

/*fct for the sockets*/
void set_nonblocking(int fd) {
    int flags = fcntl(fd, F_GETFL, 0);
    fcntl(fd, F_SETFL, flags | O_NONBLOCK);
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

    // Accept an incoming connection
    if ((client_fd = accept(server_fd, (struct sockaddr *)&address, (socklen_t*)&addrlen)) < 0) {
        perror("accept");
        close(server_fd);
        exit(EXIT_FAILURE);
    }

    // Set the socket to non-blocking mode
    set_nonblocking(client_fd);
}

void close_socket() {
    close(client_fd);
    close(server_fd);
}

void listen_to_socket() {
    fd_set read_fds;
    struct timeval timeout;

    FD_ZERO(&read_fds);
    FD_SET(client_fd, &read_fds);

    timeout.tv_sec = 1;
    timeout.tv_usec = 0;

    int activity = select(client_fd + 1, &read_fds, NULL, NULL, &timeout);

    if (activity < 0) {
        perror("select");
    } else if (activity > 0 && FD_ISSET(client_fd, &read_fds)) {
        // Read data from the client
        int bytes_read = read(client_fd, buffer, BUFFER_SIZE);
        if (bytes_read > 0) {
            buffer[bytes_read] = '\0'; // Null-terminate the received string
            printf("Received from client: %s\n", buffer);
            strcpy(message, buffer);

            // Send a response back to the client
            char *response = "Hello from C server!";
            write(client_fd, response, strlen(response));

            if (strcmp(buffer, "0") == 0) {
                loop = 0;
            }
        }
    }
    else{
        strcpy(message, "");
    }
}


void check_domain1_state(void)
{
    ec_domain_state_t ds;

    ecrt_domain_state(domain1, &ds);

    if (ds.working_counter != domain1_state.working_counter) {
        printf("Domain1: WC %u.\n", ds.working_counter);
    }
    if (ds.wc_state != domain1_state.wc_state) {
        printf("Domain1: State %u.\n", ds.wc_state);
    }

    domain1_state = ds;
}

/*****************************************************************************/

void check_master_state(void)
{
    ec_master_state_t ms;

    ecrt_master_state(master, &ms);

    if (ms.slaves_responding != master_state.slaves_responding) {
        printf("%u slave(s).\n", ms.slaves_responding);
    }
    if (ms.al_states != master_state.al_states) {
        printf("AL states: 0x%02X.\n", ms.al_states);
    }
    if (ms.link_up != master_state.link_up) {
        printf("Link is %s.\n", ms.link_up ? "up" : "down");
    }

    master_state = ms;
}

/*****************************************************************************/

void check_slave_config_states(void)
{
    ec_slave_config_state_t s;

    ecrt_slave_config_state(sc_ana_in, &s);

    if (s.al_state != sc_ana_in_state.al_state) {
        printf("AnaIn: State 0x%02X.\n", s.al_state);
    }
    if (s.online != sc_ana_in_state.online) {
        printf("AnaIn: %s.\n", s.online ? "online" : "offline");
    }
    if (s.operational != sc_ana_in_state.operational) {
        printf("AnaIn: %soperational.\n", s.operational ? "" : "Not ");
    }

    sc_ana_in_state = s;
}

/*****************************************************************************/

void cyclic_task()
{
    // receive process data
    ecrt_master_receive(master);
    ecrt_domain_process(domain1);

    // check process data state
    check_domain1_state();

    listen_to_socket();

    //check updates from the GUI
    if (message[0] != '\0'){
        decodeMessage(message);//here the IPC will have to be added
        /*
        //check if the state if 0 to kill program
        if (!state){
            //maybe turning off everythin properly first
            
            //digital write
            EC_WRITE_U8(domain1_pd + off_dig_out1, 0x00);
            //EC_WRITE_U8(domain1_pd + off_dig_out2, 0x00 );

            //analog write // a slow decrease might be needed 
            EC_WRITE_U16(domain1_pd + off_ana_out1, 0);
            EC_WRITE_U16(domain1_pd + off_ana_out2, 0);
            printf("Terminating cycle...");

            loop=0;//will add a flag here to terminate the while loop in the main

            return;//exit the program
        }

        // Read the current value at the address
        uint16_t current_ana1 = EC_READ_U16(domain1_pd + off_ana_out1);
        uint16_t current_ana2 = EC_READ_U16(domain1_pd + off_ana_out2);
        uint8_t current_dig = EC_READ_U8(domain1_pd + off_dig_out1);
        uint8_t current_dig1 = current_dig%2;
        uint8_t current_dig2 = (current_dig- current_dig1)%2;

        // Compare with the new value and write if needed
        if (current_ana1 != ana1) {
            EC_WRITE_U16(domain1_pd + off_ana_out1, ana1);
        }
        if (current_ana2 != ana2) {
            EC_WRITE_U16(domain1_pd + off_ana_out2, ana2);
        }
        if (current_dig1 != dig1) {
            if(dig1){
                current_dig=current_dig | 0x01;
            }
            else{
                current_dig=current_dig ^ 0x01;
            }
            EC_WRITE_U8(domain1_pd + off_dig_out1, current_dig);
        }
        
        if (current_dig2 != dig2) {
            if(dig2){
                current_dig=current_dig | 0x02;
            }
            else{
                current_dig=current_dig ^ 0x02;
            }
            EC_WRITE_U8(domain1_pd + off_dig_out1, current_dig);
        }
        */
    }
    
    if (counter) {
        counter--;
    }
    else { // do this at 1 Hz
        counter = FREQUENCY;

        // calculate new process data
        blink = !blink;
        /*
        //check sent signals
        uint16_t check_ana1 = EC_READ_U16(domain1_pd + off_ana_out1);
        uint16_t check_ana2 = EC_READ_U16(domain1_pd + off_ana_out2);
        uint8_t check_dig1 = EC_READ_U8(domain1_pd + off_dig_out1);
        uint8_t check_dig2 = EC_READ_U8(domain1_pd + off_dig_out1);*/
        printf("Check Analog Output 1: %f and Analog Output 2: %f\n", ana1, ana2);
        printf("Check Digital Output 1: %u and Digital Output 2: %u and Digital Output 3: %u\n", dig1, dig2, dig3);


        //Analog read
        /*
        uint16_t ana_in_value1 = EC_READ_U16(domain1_pd + off_ana_in1);
        uint16_t ana_in_value2 = EC_READ_U16(domain1_pd + off_ana_in2);
        printf("Input1 : %u and Input 2: %u\n", ana_in_value1, ana_in_value2);
        */
        // check for master state (optional)
        check_master_state();

        // check for slave configuration state(s) (optional)
        check_slave_config_states();
    }



    // send process data
    ecrt_domain_queue(domain1);
    ecrt_master_send(master);
}
/****************************************************************************/

void stack_prefault(void)
{
    unsigned char dummy[MAX_SAFE_STACK];

    memset(dummy, 0, MAX_SAFE_STACK);
}

/****************************************************************************/

int main()
{
    ec_slave_config_t *sc;
    struct timespec wakeup_time;
    int ret = 0;

    master = ecrt_request_master(0);
    if (!master) {
        return -1;
    }

    domain1 = ecrt_master_create_domain(master);
    if (!domain1) {
        return -1;
    }

    if (!(sc_ana_in = ecrt_master_slave_config(
                    master, AnaInSlavePos, Beckhoff_EL3164))) {
        fprintf(stderr, "Failed to get slave configuration.\n");
        return -1;
    }

    printf("Configuring PDOs...\n");
    if (ecrt_slave_config_pdos(sc_ana_in, EC_END, slave_3_syncs)) {
        fprintf(stderr, "Failed to configure PDOs.\n");
        return -1;
    }

    if (!(sc = ecrt_master_slave_config(
                    master, AnaOutSlavePos, Beckhoff_EL4104))) {
        fprintf(stderr, "Failed to get slave configuration.\n");
        return -1;
    }

    if (ecrt_slave_config_pdos(sc, EC_END, slave_2_syncs)) {
        fprintf(stderr, "Failed to configure PDOs.\n");
        return -1;
    }

    if (!(sc = ecrt_master_slave_config(
                    master, DigOutSlavePos, Beckhoff_EL2024))) {
        fprintf(stderr, "Failed to get slave configuration.\n");
        return -1;
    }

    if (ecrt_slave_config_pdos(sc, EC_END, slave_1_syncs)) {
        fprintf(stderr, "Failed to configure PDOs.\n");
        return -1;
    }

    // Create configuration for bus coupler
    sc = ecrt_master_slave_config(master, BusCouplerPos, Beckhoff_EK1100);
    if (!sc) {
        return -1;
    }

    if (ecrt_domain_reg_pdo_entry_list(domain1, domain1_regs)) {
        fprintf(stderr, "PDO entry registration failed!\n");
        return -1;
    }

    printf("Activating master...\n");
    if (ecrt_master_activate(master)) {
        return -1;
    }

    if (!(domain1_pd = ecrt_domain_data(domain1))) {
        return -1;
    }

    /* Set priority */

    struct sched_param param = {};
    param.sched_priority = sched_get_priority_max(SCHED_FIFO);

    printf("Using priority %i.", param.sched_priority);
    if (sched_setscheduler(0, SCHED_FIFO, &param) == -1) {
        perror("sched_setscheduler failed");
    }

    /* Lock memory */

    if (mlockall(MCL_CURRENT | MCL_FUTURE) == -1) {
        fprintf(stderr, "Warning: Failed to lock memory: %s\n",
                strerror(errno));
    }

    stack_prefault();

    printf("Starting RT task with dt=%u ns.\n", PERIOD_NS);

    //socket start
    start_socket();

    clock_gettime(CLOCK_MONOTONIC, &wakeup_time);
    wakeup_time.tv_sec += 1; /* start in future */
    wakeup_time.tv_nsec = 0;

    while (loop) {
        ret = clock_nanosleep(CLOCK_MONOTONIC, TIMER_ABSTIME,
                &wakeup_time, NULL);
        if (ret) {
            fprintf(stderr, "clock_nanosleep(): %s\n", strerror(ret));
            break;
        }

        cyclic_task();

        wakeup_time.tv_nsec += PERIOD_NS;
        while (wakeup_time.tv_nsec >= NSEC_PER_SEC) {
            wakeup_time.tv_nsec -= NSEC_PER_SEC;
            wakeup_time.tv_sec++;
        }
    }

    close_socket();
    return ret;
}

/****************************************************************************/
