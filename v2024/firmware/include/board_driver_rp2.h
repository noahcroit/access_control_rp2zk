#ifndef BOARD_DRIVER_RP2_H
#define BOARD_DRIVER_RP2_H

#include <stdio.h>
#include "pico/stdlib.h"
#include "pico/cyw43_arch.h"
#define DEBUG 1
#define TOTAL_NUM_GPIO_RP2 32

// serial print and sleep function
#if DEBUG == 1
#define driver_debug_print(x) printf(x)
#else
#define driver_debug_print(x)
#endif

#define driver_sleep_ms(x) sleep_ms(x)



void driver_rp2_sysinit();
void driver_rp2_set_gpio_input(uint8_t gpio_num);
void driver_rp2_set_gpio_output(uint8_t gpio_num);
bool driver_rp2_read_gpio(uint8_t gpio_num);
void driver_rp2_write_gpio(uint8_t gpio_num, bool value);
void driver_rp2_enable_gpio_global_interrupt();
void driver_rp2_set_gpio_callback(uint8_t gpio_num, void (*cb) (void));

#endif
