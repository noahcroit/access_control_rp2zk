#include "board_driver_rp2.h"



// array of GPIO callback functions
static void (*gpio_cb[TOTAL_NUM_GPIO_RP2]) (void);

// ISR for GPIO
static void isr_gpio(uint gpio, uint32_t events) {
    gpio_cb[gpio]();
}



void driver_rp2_sysinit() {
    // Use printf as serial print on USB
    stdio_init_all();
}

void driver_rp2_set_gpio_input(uint8_t gpio_num) {
    // Direction and pull-up setup
    gpio_set_function(gpio_num, GPIO_FUNC_SIO);
    gpio_set_dir(gpio_num, GPIO_IN);
    gpio_pull_up(gpio_num);
    
    // Enable an interrupt for target pin
    gpio_set_irq_enabled (gpio_num, GPIO_IRQ_EDGE_FALL, true);
}

void driver_rp2_enable_gpio_global_interrupt() {
    irq_set_enabled(IO_IRQ_BANK0, true);
    gpio_set_irq_callback (isr_gpio);
}

void driver_rp2_set_gpio_callback(uint8_t gpio_num, void (*cb) (void)) {
    gpio_cb[gpio_num] = cb;
}

bool driver_rp2_read_gpio(uint8_t gpio_num) {
    bool value;
    value = gpio_get(gpio_num);
    return value;
}

void driver_rp2_set_gpio_output(uint8_t gpio_num) {
    // Direction and pull-up setup
    gpio_set_function(gpio_num, GPIO_FUNC_SIO);
    gpio_set_dir(gpio_num, GPIO_OUT);
    gpio_disable_pulls(gpio_num);
}

void driver_rp2_write_gpio(uint8_t gpio_num, bool value) {
    gpio_put(gpio_num, value);
}

