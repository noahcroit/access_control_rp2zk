#ifndef APP_MQTT_H
#define APP_MQTT_H

#include "board_driver_rp2.h"
#include "lwip/pbuf.h"
#include "lwip/tcp.h"
#include "lwip/dns.h"
#include "lwip/apps/mqtt.h"

#define MQTT_STATE_NOT_CONNECTED 0
#define MQTT_STATE_CONNECTING 1
#define MQTT_STATE_CONNECTED 2

typedef struct {
    int8_t state;
    bool isconnected;
}app_mqtt_status_t;

#endif
