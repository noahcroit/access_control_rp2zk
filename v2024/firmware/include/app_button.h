#ifndef APP_BUTTON_H
#define APP_BUTTON_H

#include "board_driver_rp2.h"

typedef struct {
    bool (*driver_read_gpio) (uint8_t);
    void (*driver_set_gpio_input) (uint8_t, bool);
    void (*driver_enable_gpio_global_interrupt) (void);
    void (*driver_set_gpio_callback) (uint8_t, void (*) (void));
    void (*cb_onboard) (void);
    void (*cb_exit) (void);
    uint8_t gpio_num_onboard_button;
    uint8_t gpio_num_exit_button;
    uint8_t gpio_num_dipsw1;
    uint8_t gpio_num_dipsw2;
    uint8_t gpio_num_dipsw3;
    uint8_t gpio_num_dipsw4;

}app_button_t;

void app_button_init(app_button_t *dev);
bool app_is_button_pressed_onboard(app_button_t *dev);
bool app_is_button_pressed_exit(app_button_t *dev);
uint8_t app_read_dipswitch(app_button_t *dev);

#endif
