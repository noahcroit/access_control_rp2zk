#include <stdio.h>
#include "board_driver_rp2.h"
#include "app_button.h"
#include "app_led.h"
#include "app_buzzer.h"
#include "app_dsk4t100.h"
#include "app_outage.h"
#include "app_accessctrl.h"
#define PERIOD_GLOBAL_TICK_MS (uint32_t)1000
#define STATE_IDLE 1
#define STATE_ACTIVE 2  // when outage occured, fail-secure activates
#define EXIT_DELAY_STARTVALUE 30
#define DIPSWITCH_MODE_SILENT_BUZZER 1

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
    .cb_exit = on_button_pressed_exit,
    .gpio_num_exit_button = DI_EXITBUTTON,
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
    .threshold = THRESHOLD_COUNT_OUTAGE
};

app_accessctrl_t ac = {
    .driver_write_gpio = driver_rp2_write_gpio,
    .driver_set_gpio_output = driver_rp2_set_gpio_output,
    .gpio_num_slidedoor = DO_DOORLOCK,
    .lockstate = false
};

uint8_t state=STATE_IDLE;
bool flag_exit_button=false;


/*
 * main loop
 *
 */
int main() {
    // system initalize
    driver_rp2_sysinit();
    driver_rp2_create_global_tick(PERIOD_GLOBAL_TICK_MS);

    // App initialize
    app_button_init(&button);
    app_led_init(&led);
    app_buzzer_init(&buzzer);
    app_dsk4t100_init(&locker);
    app_accessctrl_init(&ac);
    app_outage_init(&outage);
    
    uint8_t exit_cnt=0;
    while (1){
        driver_sleep_ms(250);
        switch (state) {
            case STATE_IDLE:
                // task : monitor an outage event
                if(app_is_outage_occured(&outage)) {
                    app_led_y_on(&led);
                    app_led_b_off(&led);
                    app_dsk4t100_lock(&locker);
                    if (app_read_dipswitch(&button) !=  DIPSWITCH_MODE_SILENT_BUZZER) {
                        app_buzzer_on(&buzzer);
                    }
                    flag_exit_button = false;
                    state = STATE_ACTIVE;
                }
                else {
                    app_dsk4t100_unlock(&locker);
                }
                
                // task : WiFi & MQTT connection


                // task : check slidedoor lock/unlock request from access control SW
                if(app_accessctrl_is_unlock_requested(&ac)) {
                    app_accessctrl_unlock(&ac);
                    app_led_b_off(&led);
                }
                if(app_accessctrl_is_lock_requested(&ac)) {
                    app_accessctrl_lock(&ac);
                    app_led_b_on(&led);
                }

                break;

            case STATE_ACTIVE:
                // task : monitor EXIT button
                if(flag_exit_button) {
                    app_dsk4t100_unlock(&locker);
                    exit_cnt = EXIT_DELAY_STARTVALUE;
                    flag_exit_button = false;
                }
                if(exit_cnt > 0) {
                    exit_cnt--;
                    if(exit_cnt == 0) {
                        app_dsk4t100_lock(&locker);
                    }
                }

                // task : monitor outage, if power is returned or not.
                if(!app_is_outage_occured(&outage)) {
                    app_led_y_off(&led);
                    app_dsk4t100_unlock(&locker);
                    app_buzzer_off(&buzzer);
                    state = STATE_IDLE;
                }

                break;
        } // End-of-Switch
    }
    return 0;
}



/*
 * Callback functions for apps
 *
 */
void on_button_pressed_exit(){
    driver_debug_print("Exit button is pressed!\n");
    flag_exit_button = true;
}
