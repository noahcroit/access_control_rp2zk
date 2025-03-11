#include "app_button.h"



void app_button_init(app_button_t *dev) {
    // GPIO basic input setup
    dev->driver_set_gpio_input(dev->gpio_num_onboard_button);
    dev->driver_set_gpio_input(dev->gpio_num_exit_button);
    dev->driver_set_gpio_input(dev->gpio_num_dipsw1);
    dev->driver_set_gpio_input(dev->gpio_num_dipsw2);
    dev->driver_set_gpio_input(dev->gpio_num_dipsw3);
    dev->driver_set_gpio_input(dev->gpio_num_dipsw4);
    
    // Interrupt setup for pressing event
    dev->driver_enable_gpio_global_interrupt();
    dev->driver_set_gpio_callback(dev->gpio_num_onboard_button, dev->cb_onboard);
    dev->driver_set_gpio_callback(dev->gpio_num_exit_button, dev->cb_exit);
}

bool app_is_button_pressed_onboard(app_button_t *dev) {
    return !(dev->driver_read_gpio(dev->gpio_num_onboard_button));
}

bool app_is_button_pressed_exit(app_button_t *dev) {
    return !(dev->driver_read_gpio(dev->gpio_num_exit_button));
}

uint8_t app_read_dipswitch(app_button_t *dev) {
    uint8_t sw[4];
    sw[0] = dev->driver_read_gpio(dev->gpio_num_dipsw1);
    sw[1] = dev->driver_read_gpio(dev->gpio_num_dipsw2);
    sw[2] = dev->driver_read_gpio(dev->gpio_num_dipsw3);
    sw[3] = dev->driver_read_gpio(dev->gpio_num_dipsw4);
    return (sw[3] << 3) | (sw[2] << 2) | (sw[1] << 1) | (sw[0] << 0);
}

