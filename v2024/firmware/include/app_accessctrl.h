#ifndef APP_ACCESSCTRL_H
#define APP_ACCESSCTRL_H

#include "board_driver_rp2.h"

typedef struct {
    void (*driver_write_gpio) (uint8_t, bool);
    void (*driver_set_gpio_output) (uint8_t);
    uint8_t gpio_num_slidedoor;
    bool lockstate;
    bool lockrequested;
    bool unlockrequested;

}app_accessctrl_t;

void app_accessctrl_init(app_accessctrl_t *dev);
void app_accessctrl_close(app_accessctrl_t *dev);
void app_accessctrl_open(app_accessctrl_t *dev);

#endif
