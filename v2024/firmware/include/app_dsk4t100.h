#ifndef APP_DSK4T100_H
#define APP_DSK4T100_H

#include "board_driver_rp2.h"

typedef struct {
    bool (*driver_read_gpio) (uint8_t);
    bool (*driver_write_gpio) (uint8_t, bool);
    void (*driver_set_gpio_input) (uint8_t);
    void (*driver_set_gpio_output) (uint8_t);
    uint8_t gpio_num_lockctrl;
    uint8_t gpio_num_lockstatus;
    uint8_t gpio_num_doorstatus;
    bool lockstate;

}app_dsk4t100_t;

void app_dsk4t100_init(app_dsk4t100_t *dev);
void app_dsk4t100_lock(app_dsk4t100_t *dev);
void app_dsk4t100_unlock(app_dsk4t100_t *dev);
bool app_dsk4t100_is_open(app_dsk4t100_t *dev);
bool app_dsk4t100_is_actual_lock(app_dsk4t100_t *dev);

#endif
