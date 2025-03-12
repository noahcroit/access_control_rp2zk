#include "app_accessctrl.h"



void app_accessctrl_init(app_accessctrl_t *dev) {
    // GPIO basic input setup
    dev->driver_set_gpio_output(dev->gpio_num_slidedoor);
    app_accessctrl_unlock(dev);
}

void app_accessctrl_lock(app_accessctrl_t *dev) {
    dev->driver_write_gpio(dev->gpio_num_slidedoor, true);
    dev->lockstate = true;
}

void app_accessctrl_unlock(app_accessctrl_t *dev) {
    dev->driver_write_gpio(dev->gpio_num_slidedoor, false);
    dev->lockstate = false;
}

bool app_accessctrl_is_lock_requested(app_accessctrl_t *dev) {
   return false; 
}

bool app_accessctrl_is_unlock_requested(app_accessctrl_t *dev) {
   return false; 
}
