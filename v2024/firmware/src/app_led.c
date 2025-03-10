#include "app_led.h"




void app_led_init(app_led_t *dev) {
    // GPIO basic input setup
    dev->driver_set_gpio_output(dev->gpio_num_led_y);
    dev->driver_set_gpio_output(dev->gpio_num_led_b);
    app_led_y_off(dev);
    app_led_b_off(dev);
}

void app_led_y_on(app_led_t *dev) {
    dev->driver_write_gpio(dev->gpio_num_led_y, true);
    dev->onstate_led_y = true;
}

void app_led_b_on(app_led_t *dev) {
    dev->driver_write_gpio(dev->gpio_num_led_b, true);
    dev->onstate_led_b = true;
}

void app_led_y_off(app_led_t *dev) {
    dev->driver_write_gpio(dev->gpio_num_led_y, false);
    dev->onstate_led_y = false;
}

void app_led_b_off(app_led_t *dev) {
    dev->driver_write_gpio(dev->gpio_num_led_b, false);
    dev->onstate_led_b = false;
}
