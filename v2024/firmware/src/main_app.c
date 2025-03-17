#include <stdio.h>
#include <string.h>
#include "board_driver_rp2.h"
#include "app_button.h"
#include "app_led.h"
#include "app_buzzer.h"
#include "app_dsk4t100.h"
#include "app_outage.h"
#include "app_accessctrl.h"
#include "app_mqtt.h"

#define PERIOD_GLOBAL_TICK_MS (uint32_t)1000
#define STATE_IDLE 1
#define STATE_ACTIVE 2  // when outage occured, fail-secure activates
#define EXIT_DELAY_STARTVALUE 30
#define DIPSWITCH_MODE_SILENT_BUZZER 1
#define WATCHDOG_TIME_MS (uint32_t)5000

/*
 * Callback functions for apps 
 *
 */
void on_button_pressed_onboard();
void on_button_pressed_exit();
void on_mqtt_connection(mqtt_client_t* client, void* arg, mqtt_connection_status_t status);
void on_mqtt_sub_request(void *arg, err_t err);
void on_mqtt_incoming_publish(void *arg, const char *topic, u32_t tot_len);
void on_mqtt_incoming_data(void *arg, const u8_t *data, u16_t len, u8_t flags);
void on_mqtt_pub_request(void *arg, err_t result);

/*
 * MQTT functions for apps. It can't be wrapped in app-layer (app_mqtt.c) because of IwIP doesn't allow to.
 *
 */
void app_mqtt_connect(mqtt_client_t* client);
void app_mqtt_publish(mqtt_client_t *client, const char *pub_topic, char *pub_payload);

/*
 * Struct for all devices
 *
 */
app_button_t button = {
    .driver_read_gpio = driver_rp2_read_gpio,
    .driver_set_gpio_input = driver_rp2_set_gpio_input,
    .driver_enable_gpio_global_interrupt = driver_rp2_enable_gpio_global_interrupt,
    .driver_set_gpio_callback = driver_rp2_set_gpio_callback,
    .cb_exit = on_button_pressed_exit,
    .gpio_num_exit_button = DI_EXITBUTTON,
    .gpio_num_dipsw1 = DI_SW1,
    .gpio_num_dipsw2 = DI_SW2,
    .gpio_num_dipsw3 = DI_SW3,
    .gpio_num_dipsw4 = DI_SW4
};

app_led_t led = {
    .driver_write_gpio = driver_rp2_write_gpio,
    .driver_set_gpio_output = driver_rp2_set_gpio_output,
    .gpio_num_led_y = DO_LED_Y,
    .gpio_num_led_b = DO_LED_B
};

app_buzzer_t buzzer = {
    .driver_write_gpio = driver_rp2_write_gpio,
    .driver_set_gpio_output = driver_rp2_set_gpio_output,
    .gpio_num = DO_BUZZER
};

app_dsk4t100_t locker = {
    .driver_read_gpio = driver_rp2_read_gpio,
    .driver_write_gpio = driver_rp2_write_gpio,
    .driver_set_gpio_input = driver_rp2_set_gpio_input,
    .driver_set_gpio_output = driver_rp2_set_gpio_output,
    .gpio_num_lockctrl = DO_DOORLOCK,
    .gpio_num_lockstatus = DI_LOCKSTATUS,
    .gpio_num_doorstatus = DI_DOORSTATUS
};

app_outage_t outage = {
    .driver_read_gpio = driver_rp2_read_gpio,
    .driver_set_gpio_input = driver_rp2_set_gpio_input,
    .driver_enable_gpio_global_interrupt = driver_rp2_enable_gpio_global_interrupt,
    .driver_set_gpio_callback = driver_rp2_set_gpio_callback,
    .gpio_num = DI_ZEROCROSS,
    .threshold = THRESHOLD_COUNT_OUTAGE
};

app_accessctrl_t ac = {
    .driver_write_gpio = driver_rp2_write_gpio,
    .driver_set_gpio_output = driver_rp2_set_gpio_output,
    .gpio_num_slidedoor = DO_ACCESSCTRLLOCK,
    .lockstate = false,
    .lockrequested = false,
    .unlockrequested = false
};

mqtt_client_t* mqttc_lwip;
const char *WIFI_SSID = "";
const char *WIFI_PWD = "";
const int WIFI_CONNECTING_TIMEOUT_MS = 10000;
const char *USER_MQTT_BROKER = "192.168.8.102";
const int USER_MQTT_PORT = 1883;
const char *MQTT_TOPIC_ISOPENED = "door1/isopened";
const char *MQTT_TOPIC_ISLOCKED = "door1/islocked";
const char *MQTT_TOPIC_LOCKCTRL = "door1/lockctrl";
const char *MQTT_CLIENT_ID = "picow1";
const int MQTT_PUBLISH_PERIOD_SEC = 60; 
app_mqtt_status_t mqtt = {
    .state = MQTT_STATE_NOT_CONNECTED,
    .isconnected = false
};

uint8_t state=STATE_IDLE;
bool flag_exit_button=false;
uint8_t incoming_message_id=0;
const uint8_t MESSAGE_ID_TOPIC_LOCKCTRL = 1;
const uint8_t MESSAGE_ID_TOPIC_OTHERS = 0;


/*
 * main loop
 *
 */
int main() {
    // system initalize
    driver_rp2_sysinit();
    driver_rp2_create_global_tick(PERIOD_GLOBAL_TICK_MS);

    // App initialize
    app_button_init(&button);
    app_led_init(&led);
    app_buzzer_init(&buzzer);
    app_dsk4t100_init(&locker);
    app_accessctrl_init(&ac);
    app_outage_init(&outage);

    // WiFi initialize
    driver_rp2_enable_wifi();
    driver_rp2_connect_to_wifi(WIFI_SSID,
                                WIFI_PWD, 
                                WIFI_CONNECTING_TIMEOUT_MS
                                );
    
    // MQTT client initialize
    mqttc_lwip = mqtt_client_new();
    
    // Enable watchdog
    driver_rp2_watchdog_enable(WATCHDOG_TIME_MS);
    
    uint8_t exit_cnt=0;
    uint32_t current_tick=0;
    uint32_t tick_previous_pub=0;
    while (1){
        current_tick = driver_rp2_get_global_tick();
        driver_sleep_ms(250);
        switch (state) {
            case STATE_IDLE:
                // task : monitor an outage event
                if(app_is_outage_occured(&outage)) {
                    app_led_y_on(&led);
                    app_dsk4t100_lock(&locker);
                    if (app_read_dipswitch(&button) !=  DIPSWITCH_MODE_SILENT_BUZZER) {
                        app_buzzer_on(&buzzer);
                    }
                    flag_exit_button = false;
                    state = STATE_ACTIVE;
                    break;
                }
                else {
                    app_dsk4t100_unlock(&locker);
                }

                // task : WiFi & MQTT connection
                if(driver_rp2_is_wifi_connected()) {
                    if(!mqtt.isconnected) {
                        app_led_b_off(&led);
                        // run connect only 1 time when in MQTT disconnected state
                        if(mqtt.state != MQTT_STATE_CONNECTING) {
                            app_mqtt_connect(mqttc_lwip);
                            mqtt.state = MQTT_STATE_CONNECTING;
                        }
                    }
                    else{
                        app_led_b_on(&led);
                        // MQTT publish routine for device status
                        uint32_t diff;
                        if(current_tick >= tick_previous_pub) {
                            diff = current_tick - tick_previous_pub;
                        }
                        else {
                            diff = (0xffffffff - tick_previous_pub) + current_tick + 1;
                        }
                        if(diff >= MQTT_PUBLISH_PERIOD_SEC) {
                            // publish cmd
                            char payload[2] = "N";
                            if(app_dsk4t100_is_open(&locker)) payload[0] = 'Y';
                            else payload[0] = 'N';
                            app_mqtt_publish(mqttc_lwip, MQTT_TOPIC_ISOPENED, payload);
                            // update task's tick
                            tick_previous_pub = current_tick;
                        }
                    }
                }
                else{
                    app_led_b_off(&led);
                    // reconnecting the WIFI
                    driver_rp2_connect_to_wifi(WIFI_SSID,
                                                WIFI_PWD,
                                                WIFI_CONNECTING_TIMEOUT_MS
                                                );
                }

                // task : check slidedoor lock/unlock request from access control SW
                if(app_accessctrl_is_unlock_requested(&ac)) {
                    app_accessctrl_unlock(&ac);
                    driver_debug_print("AC UNLOCK\n");
                }
                if(app_accessctrl_is_lock_requested(&ac)) {
                    app_accessctrl_lock(&ac);
                    driver_debug_print("AC LOCK\n");
                }
                break;

            case STATE_ACTIVE:
                // task : monitor EXIT button
                if(flag_exit_button) {
                    app_dsk4t100_unlock(&locker);
                    exit_cnt = EXIT_DELAY_STARTVALUE;
                    flag_exit_button = false;
                }
                if(exit_cnt > 0) {
                    exit_cnt--;
                    if(exit_cnt == 0) {
                        app_dsk4t100_lock(&locker);
                    }
                }
                // task : monitor outage, if power is returned or not.
                if(!app_is_outage_occured(&outage)) {
                    app_led_y_off(&led);
                    app_dsk4t100_unlock(&locker);
                    app_buzzer_off(&buzzer);
                    state = STATE_IDLE;
                }
                break;
        } // End-of-Switch
        
        // watchdog feed
        driver_rp2_watchdog_feed();
    }
    return 0;
}



/*
 * Callback functions for apps
 *
 */
void on_button_pressed_exit(){
    driver_debug_print("Exit button is pressed!\n");
    flag_exit_button = true;
}

void on_mqtt_connection(mqtt_client_t* client, void* arg, mqtt_connection_status_t status) {
    err_t err;
    driver_debug_print("cb is called!\n");
    if (status == MQTT_CONNECT_ACCEPTED) {
        driver_debug_print("mqtt_connection_cb: Successfully connected\n");
        mqtt.isconnected = true;
        mqtt.state = MQTT_STATE_CONNECTED;

        /*
         * Run subscribe after device is connected
         */
        mqtt_sub_unsub(client, MQTT_TOPIC_LOCKCTRL, 0, on_mqtt_sub_request, 0, 1);
        mqtt_set_inpub_callback(client, on_mqtt_incoming_publish, on_mqtt_incoming_data, 0);
    } 
    else {
        driver_debug_print("mqtt_connection_cb: Disconnected, reason: ");
        driver_debug_print_int(status);
        driver_debug_print("\n");
        mqtt.isconnected = false;
        mqtt.state = MQTT_STATE_NOT_CONNECTED;
    }
}

void on_mqtt_sub_request(void *arg, err_t err) {
    driver_debug_print("mqtt_sub_request_cb: err ");
    driver_debug_print_int(err);
    driver_debug_print("\n");
}

void on_mqtt_incoming_publish(void *arg, const char *topic, u32_t tot_len) {
    driver_debug_print("Incoming publish at topic ");
    driver_debug_print(topic);
    driver_debug_print("\n");

    if(!strcmp(topic, MQTT_TOPIC_LOCKCTRL)) {
        incoming_message_id = MESSAGE_ID_TOPIC_LOCKCTRL;
    }
    else{
        incoming_message_id = MESSAGE_ID_TOPIC_OTHERS;
    }
}

void on_mqtt_incoming_data(void *arg, const u8_t *data, u16_t len, u8_t flags) {
    // create payload from incoming data
    char *payload = (char *)malloc(len + 1);
    memcpy(payload, data, len * sizeof(char));
    payload[len] = '\0';
    driver_debug_print("Incoming publish payload with len=");
    driver_debug_print_int(len);
    driver_debug_print(", flag=");
    driver_debug_print_int((unsigned int)flags);
    driver_debug_print("\nMQTT payload: ");
    driver_debug_print(payload);
    driver_debug_print("\n");
    
    if(incoming_message_id == MESSAGE_ID_TOPIC_LOCKCTRL) {
        if(!strcmp(payload, "ON"))       ac.lockrequested = true;
        else if(!strcmp(payload, "OFF")) ac.unlockrequested = true;
    }
    free(payload);
}

/* Called when publish is complete either with sucess or failure */
void on_mqtt_pub_request(void *arg, err_t result) {
    if(result != ERR_OK) {
        driver_debug_print("Publish result : ");
        driver_debug_print_int(result);
        driver_debug_print("\n");
    }
    else{
        driver_debug_print("cb, Publish OK\n");
    }
}

/*
 * MQTT functions
 *
 */
void app_mqtt_connect(mqtt_client_t* client) {
    struct mqtt_connect_client_info_t ci;
    err_t err;

    /* Setup an empty client info structure */
    memset(&ci, 0, sizeof(ci));

    /* Minimal amount of information required is client identifier, so set it here */
    ci.client_id = MQTT_CLIENT_ID;

    ip_addr_t mqtt_ip;
    ip4addr_aton(USER_MQTT_BROKER, &mqtt_ip);

    //cyw43_arch_lwip_begin();
    driver_debug_print("mqtt_client_connect()\n");
    err = mqtt_client_connect(mqttc_lwip, &mqtt_ip, USER_MQTT_PORT, on_mqtt_connection, 0, &ci);
    //cyw43_arch_lwip_end();

    /* For now just print the result code if something goes wrong*/
    driver_debug_print("ERR return : ");
    driver_debug_print_int(err);
    driver_debug_print("\n");
}

void app_mqtt_publish(mqtt_client_t *client, const char *pub_topic, char *pub_payload) {
    u8_t qos = 0; /* 0 1 or 2, see MQTT specification */
    u8_t retain = 0; /* No don't retain such crappy payload... */
    mqtt_publish(client, 
                pub_topic,
                pub_payload,
                strlen(pub_payload),
                qos,
                retain,
                on_mqtt_pub_request,
                NULL);
}
