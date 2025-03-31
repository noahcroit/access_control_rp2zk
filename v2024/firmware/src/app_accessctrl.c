#include "app_accessctrl.h"



void app_accessctrl_init(app_accessctrl_t *dev) {
    // GPIO basic input setup
    dev->driver_set_gpio_output(dev->gpio_num_slidedoor);
    dev->driver_write_gpio(dev->gpio_num_slidedoor, false);
}

void app_accessctrl_close(app_accessctrl_t *dev) {
    dev->driver_write_gpio(dev->gpio_num_slidedoor, false);
}

void app_accessctrl_open(app_accessctrl_t *dev) {
    dev->driver_write_gpio(dev->gpio_num_slidedoor, true);
}

