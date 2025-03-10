#ifndef APP_BUZZER_H
#define APP_BUZZER_H

#include "board_driver_rp2.h"

typedef struct {
    void (*driver_write_gpio) (uint8_t, bool);
    void (*driver_set_gpio_output) (uint8_t);
    uint8_t gpio_num;
    bool onstate;

}app_buzzer_t;

void app_buzzer_init(app_buzzer_t *dev);
void app_buzzer_on(app_buzzer_t *dev);
void app_buzzer_off(app_buzzer_t *dev);

#endif
