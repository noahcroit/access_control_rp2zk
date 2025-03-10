#ifndef APP_LED_H
#define APP_LED_H

#include "board_driver_rp2.h"

typedef struct {
    void (*driver_write_gpio) (uint8_t, bool);
    void (*driver_set_gpio_output) (uint8_t);
    uint8_t gpio_num_led_y;
    uint8_t gpio_num_led_b;
    bool onstate_led_y;
    bool onstate_led_b;

}app_led_t;

void app_led_init(app_led_t *dev);
void app_led_y_on(app_led_t *dev);
void app_led_y_off(app_led_t *dev);
void app_led_b_on(app_led_t *dev);
void app_led_b_off(app_led_t *dev);

#endif
