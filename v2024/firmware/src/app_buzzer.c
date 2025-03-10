#include "app_buzzer.h"




void app_buzzer_init(app_buzzer_t *dev) {
    // GPIO basic input setup
    dev->driver_set_gpio_output(dev->gpio_num);
    app_buzzer_off(dev);
}

void app_buzzer_on(app_buzzer_t *dev) {
    dev->driver_write_gpio(dev->gpio_num, true);
    dev->onstate = true;
}

void app_buzzer_off(app_buzzer_t *dev) {
    dev->driver_write_gpio(dev->gpio_num, false);
    dev->onstate = false;
}
