#include <stdio.h>
#include "board_driver_rp2.h"
#include "app_button.h"
#include "app_led.h"
#include "app_buzzer.h"
#include "app_dsk4t100.h"
#include "app_outage.h"
#include "app_accessctrl.h"

#define DI_ZEROCROSS 2
#define DI_USERBUTTON 10
#define DI_EXITBUTTON 10
#define DI_SW1 6
#define DI_SW2 7
#define DI_SW3 8
#define DI_SW4 9
#define DO_LED_B 4
#define DO_LED_Y 5
#define DO_BUZZER 11
#define DO_DOORLOCK 18
#define DI_DOORSTATUS 19
#define DI_LOCKSTATUS 20
#define DO_SLIDEDOOR 28



/*
 * Callback functions for apps
 *
 */
void on_button_pressed_onboard();
void on_button_pressed_exit();



/*
 * Struct for all devices
 *
 */
app_button_t button = {
    .driver_read_gpio = driver_rp2_read_gpio,
    .driver_set_gpio_input = driver_rp2_set_gpio_input,
    .driver_enable_gpio_global_interrupt = driver_rp2_enable_gpio_global_interrupt,
    .driver_set_gpio_callback = driver_rp2_set_gpio_callback,
    .cb_onboard = on_button_pressed_onboard, 
    .cb_exit = on_button_pressed_exit,
    .gpio_num_onboard_button = DI_USERBUTTON,
    .gpio_num_exit_button = DI_USERBUTTON,
    .gpio_num_dipsw1 = DI_SW1,
    .gpio_num_dipsw2 = DI_SW2,
    .gpio_num_dipsw3 = DI_SW3,
    .gpio_num_dipsw4 = DI_SW4
};

app_led_t led = {
    .driver_write_gpio = driver_rp2_write_gpio,
    .driver_set_gpio_output = driver_rp2_set_gpio_output,
    .gpio_num_led_y = DO_LED_Y,
    .gpio_num_led_b = DO_LED_B
};

app_buzzer_t buzzer = {
    .driver_write_gpio = driver_rp2_write_gpio,
    .driver_set_gpio_output = driver_rp2_set_gpio_output,
    .gpio_num = DO_BUZZER
};

app_dsk4t100_t locker = {
    .driver_read_gpio = driver_rp2_read_gpio,
    .driver_write_gpio = driver_rp2_write_gpio,
    .driver_set_gpio_input = driver_rp2_set_gpio_input,
    .driver_set_gpio_output = driver_rp2_set_gpio_output,
    .gpio_num_lockctrl = DO_DOORLOCK,
    .gpio_num_lockstatus = DI_LOCKSTATUS,
    .gpio_num_doorstatus = DI_DOORSTATUS
};

app_outage_t outage = {
    .driver_read_gpio = driver_rp2_read_gpio,
    .driver_set_gpio_input = driver_rp2_set_gpio_input,
    .driver_enable_gpio_global_interrupt = driver_rp2_enable_gpio_global_interrupt,
    .driver_set_gpio_callback = driver_rp2_set_gpio_callback,
    .gpio_num = DI_ZEROCROSS,
    .threshold = 5
};

app_accessctrl_t ac = {
    .driver_write_gpio = driver_rp2_write_gpio,
    .driver_set_gpio_output = driver_rp2_set_gpio_output,
    .gpio_num_slidedoor = DO_DOORLOCK,
    .lockstate = false
};



/*
 * main loop
 *
 */
int main() {
    // system initalize
    driver_rp2_sysinit();
    driver_rp2_create_global_tick(1000);

    // App initialize
    app_button_init(&button);
    app_led_init(&led);
    app_buzzer_init(&buzzer);
    app_dsk4t100_init(&locker);
    app_accessctrl_init(&ac);
    app_outage_init(&outage);

    while (1){ 
        // button function for testing LEDs & bolt-lock
        if (app_is_button_pressed_onboard(&button)) {
            app_led_y_on(&led);
            app_buzzer_on(&buzzer);
            app_dsk4t100_unlock(&locker);
        }
        else{
            app_led_y_off(&led);
            app_buzzer_off(&buzzer);
            app_dsk4t100_lock(&locker);
        }

        // check door status from bolt-lock
        /*
        bool isopen;
        isopen = app_dsk4t100_is_open(&locker);
        driver_debug_print("door status : ");
        driver_debug_print_int(isopen);
        driver_debug_print("\n");
        */

        // check outage
        bool isoutage;
        isoutage = app_is_outage_occured(&outage);
        driver_debug_print("outage status : ");
        driver_debug_print_int(isoutage);
        driver_debug_print("\n");

        // sleep
        uint32_t tick = driver_rp2_get_global_tick();
        driver_debug_print("global tick=");
        driver_debug_print_int(tick);
        driver_debug_print("\n");
        driver_sleep_ms(1000);
    }
    return 0;
}



/*
 * Callback functions for apps
 *
 */
void on_button_pressed_onboard(){
    driver_debug_print("Onboard button is pressed!\n");
}

void on_button_pressed_exit(){
    driver_debug_print("Exit button is pressed!\n");
}
