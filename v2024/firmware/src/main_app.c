#include <stdio.h>
#include "board_driver_rp2.h"
#include "app_button.h"
#include "app_led.h"
#include "app_buzzer.h"

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



/*
 * Callback functions for apps
 *
 */
void on_button_pressed_onboard();
void on_button_pressed_exit();



app_button_t button;  
app_led_t led;  
app_buzzer_t buzzer;  



int main() {
    // system initalize
    driver_rp2_sysinit();

    // App button initialize
    button.driver_read_gpio = driver_rp2_read_gpio;
    button.driver_set_gpio_input = driver_rp2_set_gpio_input;
    button.driver_enable_gpio_global_interrupt = driver_rp2_enable_gpio_global_interrupt;
    button.driver_set_gpio_callback = driver_rp2_set_gpio_callback;
    button.cb_onboard = on_button_pressed_onboard; 
    button.cb_exit = on_button_pressed_exit; 
    button.gpio_num_onboard_button = DI_USERBUTTON;
    button.gpio_num_exit_button = DI_USERBUTTON;
    button.gpio_num_dipsw1 = DI_SW1;
    button.gpio_num_dipsw2 = DI_SW2;
    button.gpio_num_dipsw3 = DI_SW3;
    button.gpio_num_dipsw4 = DI_SW4;
    app_button_init(&button);

    // App LED initialize
    led.driver_write_gpio = driver_rp2_write_gpio;
    led.driver_set_gpio_output = driver_rp2_set_gpio_output;
    led.gpio_num_led_y = DO_LED_Y;
    led.gpio_num_led_b = DO_LED_B;
    app_led_init(&led);

    // App LED initialize
    buzzer.driver_write_gpio = driver_rp2_write_gpio;
    buzzer.driver_set_gpio_output = driver_rp2_set_gpio_output;
    buzzer.gpio_num = DO_BUZZER;
    app_buzzer_init(&buzzer);

    while (1) {
        if (app_is_button_pressed_onboard(&button)) {
            app_led_y_on(&led);
            app_buzzer_on(&buzzer);
        }
        else{
            app_led_y_off(&led);
            app_buzzer_off(&buzzer);
        }
        driver_sleep_ms(100);
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
