#ifndef APP_OUTAGE_H
#define APP_OUTAGE_H

#include "board_driver_rp2.h"
#define THRESHOLD_COUNT_OUTAGE 5

typedef struct {
    bool (*driver_read_gpio) (uint8_t);
    void (*driver_set_gpio_input) (uint8_t, bool);
    void (*driver_enable_gpio_global_interrupt) (void);
    void (*driver_set_gpio_callback) (uint8_t, void (*) (void));
    uint8_t gpio_num;
    uint32_t threshold;

}app_outage_t;

void app_outage_init(app_outage_t *dev);
bool app_is_outage_occured(app_outage_t *dev);

#endif
