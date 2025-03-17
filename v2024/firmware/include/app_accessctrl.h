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
void app_accessctrl_lock(app_accessctrl_t *dev);
void app_accessctrl_unlock(app_accessctrl_t *dev);
bool app_accessctrl_is_lock_requested(app_accessctrl_t *dev);
bool app_accessctrl_is_unlock_requested(app_accessctrl_t *dev);

#endif
