#include <stdio.h>
#include "pico/stdlib.h"
#include "pico/cyw43_arch.h"
#include "hardware/vreg.h"
#include "hardware/clocks.h"

#include "lwip/pbuf.h"
#include "lwip/tcp.h"
#include "lwip/dns.h"
#include "lwip/apps/mqtt.h"



#define GPIO_PIN_LED 10
#define WIFI_SSID "ASUS_for_ICT"
#define WIFI_PASSWORD "ictadmin"
#define INET_ADDRSTRLEN 16
#define MQTT_BROKER_ADDR "192.168.4.52"



int net_wifi_get_ipaddr (int iface, ip_addr_t *ipaddr);
void mqtt_connection_cb(mqtt_client_t* client, void* arg, mqtt_connection_status_t status);
void mqtt_connect(mqtt_client_t* client);
void example_publish(mqtt_client_t *client, void *arg);
void mqtt_pub_request_cb(void *arg, err_t result);
void mqtt_sub_request_cb(void *arg, err_t err);
void mqtt_incoming_publish_cb(void *arg, const char *topic, u32_t tot_len);
void mqtt_incoming_data_cb(void *arg, const u8_t *data, u16_t len, u8_t flags);



int net_wifi_get_ipaddr (int iface, ip_addr_t *ipaddr)
{
    if ((iface >= 0) && (iface <= 1)){
        if ( cyw43_tcpip_link_status (&cyw43_state, iface) == CYW43_LINK_UP ){
            memcpy (ipaddr, &cyw43_state.netif[iface].ip_addr, sizeof (ip_addr_t));
            return ERR_OK;
        }
        return ERR_CONN;
    }
    return ERR_ARG;
}

void mqtt_connection_cb(mqtt_client_t* client, void* arg, mqtt_connection_status_t status) {
    err_t err;
    printf("cb is called!\n");
    if (status == MQTT_CONNECT_ACCEPTED) {
        printf("mqtt_connection_cb: Successfully connected\n");
        
        /* Start subscribe here
         */
        mqtt_sub_unsub(client, "pico/recv", 0, mqtt_sub_request_cb, 0, 1);
    } 
    else {
        printf("mqtt_connection_cb: Disconnected, reason: %d\n", status);
    }
}

void mqtt_connect(mqtt_client_t* client) {
    struct mqtt_connect_client_info_t ci;
    err_t err;

    /* Setup an empty client info structure */
    memset(&ci, 0, sizeof(ci));

    /* Minimal amount of information required is client identifier, so set it here */
    ci.client_id = "test";

    /* Initiate client and connect to server, if this fails immediately an error code is returned
        otherwise mqtt_connection_cb will be called with connection result after attempting
        to establish a connection with the server.
        For now MQTT version 3.1.1 is always used */
    // 192.168.1.150:1885"
    ip_addr_t mqtt_ip;
    ip4addr_aton(MQTT_BROKER_ADDR, &mqtt_ip);

    cyw43_arch_lwip_begin();
    printf("mqtt_clent_connect()\n");
    err = mqtt_client_connect(client, &mqtt_ip, 1883, mqtt_connection_cb, 0, &ci);
    cyw43_arch_lwip_end();

    /* For now just print the result code if something goes wrong*/
    if (err != ERR_OK) {
        printf("mqtt_connect return %d\n", err);
    }
    else{
        printf("ERR_OK, err=%d\n", err);
    }
}

/* Called when publish is complete either with sucess or failure */
void mqtt_pub_request_cb(void *arg, err_t result)
{
    if(result != ERR_OK) {
        printf("Publish result: %d\n", result);
    }
    else{
        printf("cb, Publish OK\n");
    }
}

void example_publish(mqtt_client_t *client, void *arg)
{
    const char *pub_payload= "PubSubHubLubJub";
    err_t err;
    u8_t qos = 0; /* 0 1 or 2, see MQTT specification */
    u8_t retain = 0; /* No don't retain such crappy payload... */
    err = mqtt_publish(client, "test_topic", pub_payload, strlen(pub_payload), qos, retain, mqtt_pub_request_cb, arg);
    if(err != ERR_OK) {
        printf("Publish err: %d\n", err);
    }
    else{
        printf("Set Sub callback\n");
        mqtt_set_inpub_callback (client, mqtt_incoming_publish_cb, mqtt_incoming_data_cb, 0); 
    }
}

/* Subscribe callback */
void mqtt_sub_request_cb(void *arg, err_t err) {
    printf("mqtt_sub_request_cb: err %d\n", err);
}

static int inpub_id;
void mqtt_incoming_publish_cb(void *arg, const char *topic, u32_t tot_len)
{
    printf("Incoming publish at topic %s with total length %u\n", topic, (unsigned int)tot_len);
    /*
    if (topic[0] == 'A') {
        // Handle all topics starting with 'A' in the same way
        inpub_id = 1;
    } 
    else {
        // Handle all other topics differently
        inpub_id = 2;
    }
    // Handle in this demo
    inpub_id = -1;
    */
}

void mqtt_incoming_data_cb(void *arg, const u8_t *data, u16_t len, u8_t flags)
{
    printf("Incoming publish payload with length %d, flags %u\n", len, (unsigned int)flags);
    printf("mqtt payload: %s\n", (const char *)data);
    printf("***************\n\n");
    /*
    if (flags & MQTT_DATA_FLAG_LAST) {
        // Handle data based on the reference
        if (inpub_id == -1) {
            // No handling in this demo
            return;
        } 
        else if (inpub_id == 1) {
            // Handling data with topics starting with 'A'
        } 
        else {
            printf("mqtt_incoming_data_cb: Ignoring payload...\\n");
        }
    } else {
        // To handle payloads that are too long, save them in a buffer or a file.
    }
    */
}



int main() {
    ip_addr_t ipaddr;
    char str_addr[INET_ADDRSTRLEN];

    // system initalize
    stdio_init_all();
	
    /*
     * WiFi module cyw43 initialize
     *
     */
    while (cyw43_arch_init()) {
        printf("failed to initialise\n");
        sleep_ms(1000);
    }
    printf("Enable WiFi STA mode\n");
    cyw43_arch_enable_sta_mode();
    
    /*
     * WiFi connecting to access point
     *
     */
    printf("Connecting to Wi-Fi...\n");
    while (cyw43_arch_wifi_connect_timeout_ms(WIFI_SSID, WIFI_PASSWORD, CYW43_AUTH_WPA2_AES_PSK, 30000)) {
        printf("Failed to connect.\n");
        sleep_ms(1000);
    }
    printf("Connected!\n");
    net_wifi_get_ipaddr (CYW43_ITF_STA, &ipaddr);
    ip4addr_ntoa_r(&ipaddr, str_addr, INET_ADDRSTRLEN);
    printf("IPv4 Address: %s\n", str_addr);

    /*
     * MQTT
     *
     */
    mqtt_client_t* client = mqtt_client_new();
    printf("Try to connect MQTT.\n");
    mqtt_connect(client);
    printf("End.\n");

    uint32_t cnt=0;
    while (1) {
        // Check WiFi connection status & MQTT status
        if (cyw43_wifi_link_status (&cyw43_state, CYW43_ITF_STA) == CYW43_LINK_JOIN) {
            printf("Still connected, ");
            if(mqtt_client_is_connected(client)){
                printf("cnt=%d, mqtt is still connected, start to publish a msg...\n", cnt);

                // MQTT Publish
                example_publish(client, 0);
            }
            cnt++;
        }
        sleep_ms(3000);
    }
    return 0;
}

