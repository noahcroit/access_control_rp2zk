#ifndef BOARD_DRIVER_RP2_H
#define BOARD_DRIVER_RP2_H

#include <stdio.h>
#include "pico/stdlib.h"
#include "pico/cyw43_arch.h"
#include "hardware/pll.h"
#include "hardware/clocks.h"
#include "hardware/structs/pll.h"
#include "hardware/structs/clocks.h"
#define DEBUG 1
#define TOTAL_NUM_GPIO_RP2 32
#define NUM_OF_MAX_TIMER_CB 16

// serial print and sleep function
#if DEBUG == 1
#define driver_debug_print(x) printf(x)
#define driver_debug_print_int(x) printf("%d", x)
#define driver_debug_print_f32(x) printf("%f", x)
#else
#define driver_debug_print(x)
#define driver_debug_print_int(x)
#define driver_debug_print_float(x)
#endif

#define driver_sleep_ms(x) sleep_ms(x)



void driver_rp2_sysinit();
void driver_rp2_set_gpio_input(uint8_t gpio_num, bool use_interrupt);
void driver_rp2_set_gpio_output(uint8_t gpio_num);
bool driver_rp2_read_gpio(uint8_t gpio_num);
void driver_rp2_write_gpio(uint8_t gpio_num, bool value);
void driver_rp2_enable_gpio_global_interrupt();
void driver_rp2_set_gpio_callback(uint8_t gpio_num, void (*cb) (void));
void driver_rp2_create_global_tick(uint32_t tick_period_ms);
uint32_t driver_rp2_get_global_tick();

#endif
