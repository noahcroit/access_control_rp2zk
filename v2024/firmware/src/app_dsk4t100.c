#include "app_dsk4t100.h"




void app_dsk4t100_init(app_dsk4t100_t *dev) {
    // GPIO basic input setup
    dev->driver_set_gpio_output(dev->gpio_num_lockctrl);
    dev->driver_set_gpio_output(dev->gpio_num_lockstatus);
    dev->driver_set_gpio_input(dev->gpio_num_doorstatus, false);
    app_dsk4t100_unlock(dev);
}

void app_dsk4t100_lock(app_dsk4t100_t *dev) {
    dev->driver_write_gpio(dev->gpio_num_lockctrl, true);
    dev->lockstate = true;
}

void app_dsk4t100_unlock(app_dsk4t100_t *dev) {
    dev->driver_write_gpio(dev->gpio_num_lockstatus, false);
    driver_sleep_ms(500);
    dev->driver_write_gpio(dev->gpio_num_lockctrl, false);
    driver_sleep_ms(500);
    dev->driver_write_gpio(dev->gpio_num_lockstatus, true);
    dev->lockstate = false;
}

bool app_dsk4t100_is_open(app_dsk4t100_t *dev) {
    return dev->driver_read_gpio(dev->gpio_num_doorstatus);
}

bool app_dsk4t100_is_actual_lock(app_dsk4t100_t *dev) {
    return !(dev->driver_read_gpio(dev->gpio_num_lockstatus));
}
