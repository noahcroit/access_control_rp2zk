#include <stdio.h>
#include "pico/stdlib.h"
#include "pico/cyw43_arch.h"

#define DI_ZEROCROSS 2
#define DI_EXITBUTTON 10
#define DI_SW1 6
#define DI_SW2 7
#define DI_SW3 8
#define DI_SW4 9
#define DO_LED_BL 4
#define DO_LED_Y 5
#define DO_BUZZER 11
#define DO_DOORLOCK 18
#define DI_DOORSTATUS 19
#define DI_LOCKSTATUS 20



bool button_flag=false;
void isr_gpio(uint gpio, uint32_t events) {
    printf("button is pressed\n");
    button_flag=true;
}

void hwInit();


int main() {
    // system initalize
    stdio_init_all();
    hwInit();
	
    int current_led_state=0;
    int current_buzzer_state=0;
    while (1) {
        current_led_state = gpio_get(DO_LED_BL);
        gpio_put(DO_LED_BL, !current_led_state);
        gpio_put(DO_LED_Y, !current_led_state);

        if(button_flag){
            gpio_put(DO_BUZZER, !current_buzzer_state);
            gpio_put(DO_DOORLOCK, !current_buzzer_state);
            current_buzzer_state = !current_buzzer_state;
            button_flag=false;
        }
        sleep_ms(1000);
    }
    return 0;
}



void hwInit(){
    /*
     * WiFi module cyw43 initialize
     *
     */
    while (cyw43_arch_init()) {
        printf("failed to initialise\n");
        sleep_ms(1000);
    }

    /*
     * Initialize GPIO
     */
    gpio_set_function(DO_LED_BL, GPIO_FUNC_SIO);
    gpio_set_function(DO_LED_Y, GPIO_FUNC_SIO);
    gpio_set_function(DO_BUZZER, GPIO_FUNC_SIO);
    gpio_set_function(DO_DOORLOCK, GPIO_FUNC_SIO);
    gpio_set_function(DI_ZEROCROSS, GPIO_FUNC_SIO);
    gpio_set_function(DI_EXITBUTTON, GPIO_FUNC_SIO);

    gpio_set_dir(DO_LED_BL, GPIO_OUT);
    gpio_set_dir(DO_LED_Y, GPIO_OUT);
    gpio_set_dir(DO_BUZZER, GPIO_OUT);
    gpio_set_dir(DO_DOORLOCK, GPIO_OUT);
    gpio_set_dir(DI_ZEROCROSS, GPIO_IN);
    gpio_set_dir(DI_EXITBUTTON, GPIO_IN);
    gpio_pull_up(DI_ZEROCROSS);
    gpio_pull_up(DI_EXITBUTTON);

    // Interrupt Setup
    irq_set_enabled(IO_IRQ_BANK0, true);
    gpio_set_irq_enabled (DI_ZEROCROSS, GPIO_IRQ_EDGE_FALL, true);
    gpio_set_irq_enabled (DI_EXITBUTTON, GPIO_IRQ_EDGE_FALL, true);
    gpio_set_irq_callback (&isr_gpio);
}

